# train_classifier.py

from datasets import load_dataset, ClassLabel
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)

# 1. Load the HF dataset
ds = load_dataset("cnamuangtoun/resume-job-description-fit", split="train")

# 2. Rename columns for convenience
ds = ds.rename_column("resume_text", "resume") \
       .rename_column("job_description_text", "job_description") \
       .rename_column("label", "labels")

# 3. If labels are strings, encode them to integers
if not isinstance(ds.features["labels"], ClassLabel):
    ds = ds.class_encode_column("labels")

# 4. Tokenize inputs (and drop raw text fields)
tok = AutoTokenizer.from_pretrained("distilbert-base-uncased")

def preprocess(examples):
    return tok(
        examples["resume"],
        examples["job_description"],
        truncation=True,
        padding="max_length",
        max_length=512,
    )

ds = ds.map(
    preprocess,
    batched=True,
    remove_columns=["resume", "job_description"],
)

# 5. Split into train/test once
split = ds.train_test_split(test_size=0.1, seed=42)
train_ds = split["train"]
test_ds  = split["test"]

# 6. Prepare model and training arguments
num_labels = ds.features["labels"].num_classes

model = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=num_labels,
)

args = TrainingArguments(
    output_dir="models/resume-fit",
    per_device_train_batch_size=8,
    eval_strategy="steps",    # newer alias for evaluation_strategy
    eval_steps=500,
    logging_steps=500,
    num_train_epochs=5,
    save_total_limit=1,
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_ds,
    eval_dataset=test_ds,
    tokenizer=tok,
)

# 7. Train and save
trainer.train()
trainer.save_model("models/resume-fit")
tok.save_pretrained("models/resume-fit")
