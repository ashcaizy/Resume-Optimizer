from datasets import load_dataset, ClassLabel
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
)
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

# Load tokenizer and model from the saved path
model_path = "models/resume-fit"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

# Reload and preprocess dataset
ds = load_dataset("cnamuangtoun/resume-job-description-fit", split="test")
ds = ds.rename_column("resume_text", "resume") \
       .rename_column("job_description_text", "job_description") \
       .rename_column("label", "labels")

if not isinstance(ds.features["labels"], ClassLabel):
    ds = ds.class_encode_column("labels")

def preprocess(examples):
    return tokenizer(
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

# Define compute_metrics function
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc}

# Set up trainer for evaluation
trainer = Trainer(
    model=model,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)

# Run evaluation
metrics = trainer.evaluate(eval_dataset=ds)
print("Evaluation Metrics:")
print(metrics)

# Print detailed classification report
predictions = trainer.predict(ds)
y_true = predictions.label_ids
y_pred = np.argmax(predictions.predictions, axis=1)

print("\nDetailed Classification Report:")
print(classification_report(y_true, y_pred, target_names=ds.features["labels"].names))