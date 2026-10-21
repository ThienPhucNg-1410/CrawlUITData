"""Fine-tune ViSoBERT / PhoBERT (8.2–8.6). Chạy trên Colab/Kaggle GPU:
   pip install torch transformers datasets accelerate
   python -m uitconf.cli finetune --model visobert --task sentiment
"""
import json
import numpy as np

MODELS = {"phobert": "vinai/phobert-base-v2", "visobert": "uitnlp/visobert"}

def run(train, val, test, model_key, labels, text_col, label_col="label",
        seeds=(1, 2, 3), max_len=128, epochs=4, lr=3e-5, bs=16, out_dir="models_out"):
    import torch
    from datasets import Dataset
    from sklearn.metrics import f1_score
    from transformers import (AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments)

    l2i = {l: i for i, l in enumerate(labels)}
    tok = AutoTokenizer.from_pretrained(MODELS[model_key])
    def ds(d):
        x = Dataset.from_dict({"text": d[text_col].fillna("").tolist(), "labels": d[label_col].map(l2i).tolist()})
        return x.map(lambda b: tok(b["text"], truncation=True, max_length=max_len, padding="max_length"), batched=True)
    dtr, dva, dte = ds(train), ds(val), ds(test)

    counts = np.bincount(dtr["labels"], minlength=len(labels))
    w = torch.tensor(len(dtr) / (len(labels) * np.maximum(counts, 1)), dtype=torch.float)

    class WTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kw):
            y = inputs.pop("labels")
            out = model(**inputs)
            loss = torch.nn.functional.cross_entropy(out.logits, y, weight=w.to(out.logits.device))
            return (loss, out) if return_outputs else loss

    def metrics(p):
        return {"macro_f1": f1_score(p.label_ids, p.predictions.argmax(-1), average="macro")}

    results = []
    for s in seeds:
        model = AutoModelForSequenceClassification.from_pretrained(MODELS[model_key], num_labels=len(labels))
        args = TrainingArguments(output_dir=f"{out_dir}/{model_key}_s{s}", seed=s, num_train_epochs=epochs,
                                 learning_rate=lr, per_device_train_batch_size=bs, gradient_accumulation_steps=2,
                                 eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
                                 metric_for_best_model="macro_f1", fp16=torch.cuda.is_available(),
                                 report_to=[], save_total_limit=1)
        tr = WTrainer(model=model, args=args, train_dataset=dtr, eval_dataset=dva, compute_metrics=metrics)
        tr.train()
        results.append({"seed": s, "val": tr.evaluate(dva)["eval_macro_f1"],
                        "test": tr.evaluate(dte)["eval_macro_f1"]})   # test: chỉ dùng ở lần chạy cuối
    arr = np.array([r["test"] for r in results])
    summary = {"model": model_key, "runs": results, "test_macro_f1_mean": float(arr.mean()), "std": float(arr.std())}
    json.dump(summary, open(f"{out_dir}/{model_key}_summary.json", "w"), indent=2)
    return summary
