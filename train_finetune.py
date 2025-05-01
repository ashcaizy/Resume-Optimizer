#!/usr/bin/env python3
"""
train_finetune_fast.py

Lightweight fine-tuning on resume–job pairs for rapid iteration:
- Uses a smaller Flan-T5 model
- Shorter sequences
- Larger batch size, single accumulation
- Single epoch and partial dataset
- Disabled generation during eval
"""
import json
import random
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
)
import logging

# ——— LOGGING —————————————————————————————————–––––––
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ——— CONFIG —————————————————————————————————–––––––
MODEL_ID   = "google/flan-t5-small"  # smaller model
DATA_PATH  = "data/pairs.jsonl"
MAX_LEN    = 512                     # shorter sequences
TRAIN_FRAC = 0.01                     # subset of data
BATCH_SIZE = 8                       # larger batch
EPOCHS     = 1                       # single epoch
LR         = 4e-5

# ——— DEVICE —————————————————————————————————–––––––
DEVICE = "cuda" if torch.cuda.is_available() else (
         "mps" if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available() else "cpu")
logger.info(f"Using device: {DEVICE}")

# ——— LOAD DATA —————————————————————————————————–––––––
def load_records(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

records = load_records(DATA_PATH)
N = len(records)
logger.info(f"Total records: {N}")

# ——— SPLIT —————————————————————————————————–––––––
idxs = list(range(N)); random.seed(42); random.shuffle(idxs)
split = int(N * TRAIN_FRAC)
train_idx, eval_idx = idxs[:split], idxs[split:]
logger.info(f"Train: {len(train_idx)}, Eval: {len(eval_idx)}")

# ——— TOKENIZER & MODEL —————————————————————————————————–––––––
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID).to(DEVICE)
model.config.pad_token_id = tokenizer.pad_token_id

# ——— DATASET —————————————————————————————————–––––––
class Seq2SeqDataset(Dataset):
    def __init__(self, idxs, records, tokenizer, max_len):
        self.inputs = [records[i]['input'] for i in idxs]
        self.targets = [records[i]['target'] for i in idxs]
        self.tokenizer = tokenizer
        self.max_len = max_len
    def __len__(self):
        return len(self.inputs)
    def __getitem__(self, i):
        inp, tgt = self.inputs[i], self.targets[i]
        enc = self.tokenizer(
            inp,
            max_length=self.max_len,
            truncation=True,
            padding='max_length',
            return_tensors='pt',
            text_target=tgt
        )
        # fast-tokenizer provides labels; else fallback
        if 'labels' not in enc:
            enc['labels'] = self.tokenizer(tgt, max_length=self.max_len, truncation=True, padding='max_length')['input_ids']
        return {k:v.squeeze(0) for k,v in enc.items()}

train_dataset = Seq2SeqDataset(train_idx, records, tokenizer, MAX_LEN)
eval_dataset  = Seq2SeqDataset(eval_idx, records, tokenizer, MAX_LEN)

# ——— TRAINING ARGS —————————————————————————————————–––––––
training_args = Seq2SeqTrainingArguments(
    output_dir="models/fast-flant5",
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=1,
    num_train_epochs=EPOCHS,
    learning_rate=LR,
    eval_strategy="no",                  # skip eval
    predict_with_generate=False,          # speed up
    logging_steps=100,
    save_total_limit=1,
    fp16=(DEVICE=="cuda"),
    dataloader_pin_memory=False,
)

# ——— COLLATOR & TRAINER —————————————————————————————————–––––––
collator = DataCollatorForSeq2Seq(tokenizer, model=model, label_pad_token_id=-100)
trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=None,
    tokenizer=tokenizer,
    data_collator=collator,
)

# ——— MAIN —————————————————————————————————–––––––
if __name__ == '__main__':
    trainer.train()
    model.save_pretrained("models/fast-flant5")
    tokenizer.save_pretrained("models/fast-flant5")
