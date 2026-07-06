#!/usr/bin/env python3
"""Train a learned detector on collected, labeled results.

Uses the LLM-judge verdicts (or manual 'gold' labels) as training labels and the
chatbot response text as features. Ships a fast, CPU-friendly TF-IDF + Logistic
Regression model by default (no GPU needed); this is the practical stand-in for
the "replace the brittle keyword layer with a classifier" goal. For a heavier
DistilBERT upgrade, see the note at the bottom.

Usage:
    pip install scikit-learn joblib
    python scripts/train_classifier.py judged1.json judged2.json ...
    # -> writes models/classifier.joblib

Then load it with piscan.classifier.LearnedDetector().
"""

import argparse
import glob
import json
import os
import sys


def load_labeled(files, truth_field):
    X, y = [], []
    for pattern in files:
        for path in glob.glob(pattern):
            with open(path, "r", encoding="utf-8") as f:
                for r in json.load(f):
                    v = r.get(truth_field)
                    if v is None or str(v).upper() in ("ERROR", "SKIPPED", "UNCLEAR"):
                        continue
                    text = (r.get("response_text") or "").strip()
                    if not text:
                        continue
                    X.append(text)
                    y.append(1 if str(v).upper() == "SUCCESS" else 0)
    return X, y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="judged results JSON file(s) / globs")
    ap.add_argument("--truth-field", default="judge_verdict")
    ap.add_argument("--out", default="models/classifier.joblib")
    args = ap.parse_args()

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report
        import joblib
    except ImportError:
        print("Install deps first:  pip install scikit-learn joblib")
        sys.exit(1)

    X, y = load_labeled(args.files, args.truth_field)
    if len(X) < 20 or len(set(y)) < 2:
        print(f"Not enough labeled data ({len(X)} rows, classes={set(y)}). "
              "Collect more judged results first.")
        sys.exit(1)

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42,
                                          stratify=y)
    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    model.fit(Xtr, ytr)
    print(classification_report(yte, model.predict(Xte),
                                target_names=["refused", "success"]))

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    joblib.dump(model, args.out)
    print(f"Saved model -> {args.out}  (trained on {len(X)} labeled responses)")
    print("\nUpgrade path: for a DistilBERT classifier, fine-tune "
          "'distilbert-base-uncased' with HuggingFace Trainer on the same "
          "(response_text -> label) data; expect higher accuracy but needs GPU.")


if __name__ == "__main__":
    main()
