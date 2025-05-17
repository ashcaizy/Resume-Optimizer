from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)
from sklearn.metrics import precision_score, accuracy_score, recall_score, f1_score, classification_report
import numpy as np

# 1. Load and shuffle dataset
ds = load_dataset("cnamuangtoun/resume-job-description-fit", split="train")
ds = ds.shuffle(seed=42)

# 2. Rename columns
ds = ds.rename_column("resume_text", "resume") \
       .rename_column("job_description_text", "job_description") \
       .rename_column("label", "labels")

# 3. Simplify labels: "Good Fit" and "Potential Fit" → "Fit"
def simplify_label(example):
    if example["labels"] in ["Good Fit", "Potential Fit"]:
        example["labels"] = "Fit"
    return example

ds = ds.map(simplify_label)

# 4. Encode labels to two classes
ds = ds.class_encode_column("labels")
print("Label names:", ds.features["labels"].names)  # Should be ['Fit', 'No fit']

# 5. Tokenization
tok = AutoTokenizer.from_pretrained("bert-base-uncased")

def preprocess(examples):
    return tok(
        examples["resume"],
        examples["job_description"],
        truncation=True,
        padding="max_length",
        max_length=512,
    )

ds = ds.map(preprocess, batched=True, remove_columns=["resume", "job_description"])

# 6. Train/test split
split = ds.train_test_split(test_size=0.1, seed=42)
train_ds = split["train"]
test_ds  = split["test"]

# 7. Load model
model = AutoModelForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels=2,
)

# 8. Metric computation
def compute_metrics(pred):
    logits, labels = pred.predictions, pred.label_ids
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "precision": precision_score(labels, preds, zero_division=0),
        "recall": recall_score(labels, preds, zero_division=0),
        "f1": f1_score(labels, preds, zero_division=0),
    }

# 9. Training configuration
args = TrainingArguments(
    output_dir="models/resume-fit",
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    num_train_epochs=10,
    warmup_ratio=0.1,
    weight_decay=0.01,
    logging_dir="logs",
    logging_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    save_total_limit=1,
    report_to="none",
)

# 10. Trainer setup with compute_metrics
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_ds,
    eval_dataset=test_ds,
    tokenizer=tok,
    compute_metrics=compute_metrics,
)

# 11. Train and save
trainer.train()
trainer.save_model("models/resume-fit")
tok.save_pretrained("models/resume-fit")

# Evaluate on test set
metrics = trainer.evaluate(eval_dataset=test_ds)
print("\n✅ Evaluation metrics on test set after training:")
for key, value in metrics.items():
    print(f"{key}: {value:.4f}")

predictions_output = trainer.predict(test_ds)
logits = predictions_output.predictions
y_true = predictions_output.label_ids
y_pred = np.argmax(logits, axis=-1)

label_names = train_ds.features["labels"].names
print("\nDetailed classification report:")
print(classification_report(y_true, y_pred, target_names=label_names))