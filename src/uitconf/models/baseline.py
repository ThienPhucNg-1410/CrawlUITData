"""Baseline (8.1): TF-IDF (từ + ký tự) + Logistic Regression."""
import json
import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score

def run(train, val, test, text_col="text_norm", label_col="label", out_json=None):
    w = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    c = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, sublinear_tf=True)
    X = lambda d, fit=False: hstack([(w.fit_transform if fit else w.transform)(d[text_col].fillna("")),
                                     (c.fit_transform if fit else c.transform)(d[text_col].fillna(""))]).tocsr()
    Xtr = X(train, fit=True)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=2.0).fit(Xtr, train[label_col])
    res = {}
    for name, d in (("val", val), ("test", test)):
        if len(d) == 0:
            continue
        p = clf.predict(X(d))
        res[name] = {"macro_f1": f1_score(d[label_col], p, average="macro"),
                     "report": classification_report(d[label_col], p, output_dict=True, zero_division=0),
                     "confusion": confusion_matrix(d[label_col], p, labels=clf.classes_).tolist(),
                     "labels": list(clf.classes_)}
    if out_json:
        json.dump(res, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return clf, (w, c), res
