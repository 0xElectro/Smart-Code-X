#!/usr/bin/env python3
"""
hdva_agent.py

End-to-end lightweight HDVA (Hallucination Detection & Validation Agent)
- Synthetic dataset generator (for demonstration)
- Feature extraction: TF-IDF (code tokens) + AST-derived numeric features + surface features
- Classifier: RandomForestClassifier
- Training, evaluation, save/load model, demo predictions
- NEW: Command-line mode to analyze a file (--file <path>) or train model (--train)
"""

import ast
import re
import random
from collections import Counter
from typing import List, Tuple

import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, precision_recall_fscore_support
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.utils import shuffle

# ------------------------
# 1. Synthetic data generator
# ------------------------
def synthetic_real_code_snippet(i: int) -> str:
    """Generate a relatively realistic Python snippet."""
    templates = [
        "def compute_sum(nums: list[int]) -> int:\n    return sum(nums)\n",
        "class MyClass:\n    def __init__(self, x):\n        self.x = x\n    def get(self):\n        return self.x\n",
        "import math\n\ndef circle_area(r: float) -> float:\n    return math.pi * r * r\n",
        "def read_file(path):\n    with open(path, 'r') as f:\n        return f.read()\n",
        "# simple example\ndef multiply(a, b):\n    return a * b\n",
        "from collections import Counter\n\ndef top_k(items, k=3):\n    c = Counter(items)\n    return c.most_common(k)\n",
    ]
    t = random.choice(templates)
    if random.random() < 0.3:
        t += "\n# generated id: " + str(i)
    return t


def synthetic_hallucinated_code_snippet(i: int) -> str:
    """Generate synthetic 'hallucinated' code with fake APIs or logic errors."""
    patterns = [
        "def transform_data(df):\n    return df.whenify().transmute()\n",
        "from fake_lib import hypercall\n\ndef process(x):\n    return hypercall(x, mode='super')\n",
        "def compute(x):\n    return vectorized_thingy(x)\n",
        "def model_predict(data):\n    return oracle_predictor(data)\n",
        "def foo():\n    unknown = MagicTransformer().apply(foo=42)\n    return unknown\n",
    ]
    t = random.choice(patterns)
    if random.random() < 0.4:
        t = "import numpy as np\n" + t
    if random.random() < 0.2:
        t += "\n# hallucination id: " + str(i)
    return t


def synthetic_dataset(n_real: int = 400, n_hall: int = 400, seed: int = 42) -> Tuple[List[str], List[int]]:
    random.seed(seed)
    snippets, labels = [], []
    for i in range(n_real):
        snippets.append(synthetic_real_code_snippet(i))
        labels.append(0)
    for i in range(n_hall):
        snippets.append(synthetic_hallucinated_code_snippet(i))
        labels.append(1)
    snippets, labels = shuffle(snippets, labels, random_state=seed)
    return snippets, labels


# ------------------------
# 2. Feature extraction utilities
# ------------------------
def tokenize_code(code: str) -> List[str]:
    code_no_strings = re.sub(r'(\'\'\'[\s\S]*?\'\'\'|"""[\s\S]*?"""|\'[^\']*\'|"[^"]*")', ' ', code)
    tokens = re.findall(r'[A-Za-z_][A-Za-z0-9_\.]*', code_no_strings)
    return tokens


def ast_features(code: str) -> dict:
    feat = {}
    try:
        tree = ast.parse(code)
    except Exception:
        feat['ast_parsable'] = 0
        feat['num_functions'] = 0
        feat['num_classes'] = 0
        feat['num_imports'] = 0
        feat['max_depth'] = 0
        return feat

    feat['ast_parsable'] = 1
    counter = Counter()
    max_depth = 0

    def visit(node, depth=0):
        nonlocal max_depth
        counter[type(node).__name__] += 1
        max_depth = max(max_depth, depth)
        for child in ast.iter_child_nodes(node):
            visit(child, depth + 1)

    visit(tree)
    feat['num_functions'] = counter.get('FunctionDef', 0)
    feat['num_classes'] = counter.get('ClassDef', 0)
    feat['num_imports'] = counter.get('Import', 0) + counter.get('ImportFrom', 0)
    feat['max_depth'] = max_depth
    for key in ['If', 'For', 'While', 'Call', 'Assign', 'Return']:
        feat[f'ast_{key}_count'] = counter.get(key, 0)
    return feat


def surface_features(code: str) -> dict:
    lines = code.splitlines()
    n_lines = len(lines)
    n_chars = len(code)
    n_comments = sum(1 for ln in lines if ln.strip().startswith('#'))
    n_blank = sum(1 for ln in lines if not ln.strip())
    n_tokens = len(tokenize_code(code))
    return {
        'n_lines': n_lines,
        'n_chars': n_chars,
        'n_comments': n_comments,
        'n_blank': n_blank,
        'n_tokens': n_tokens,
        'comment_ratio': n_comments / max(1, n_lines),
    }


# ------------------------
# 3. Combined feature extractor
# ------------------------
class CodeFeatureExtractor:
    def __init__(self, max_features_tfidf: int = 1000):
        self.tfidf = TfidfVectorizer(
            analyzer='word',
            token_pattern=r'(?u)\b[A-Za-z_][A-Za-z0-9_\.]*\b',
            max_features=max_features_tfidf,
        )
        self.numeric_feature_names = None

    def fit(self, codes: List[str]):
        token_texts = [" ".join(tokenize_code(code)) for code in codes]
        self.tfidf.fit(token_texts)
        sample_feats = [self._numeric_features(code) for code in codes[:10]]
        all_keys = set()
        for d in sample_feats:
            all_keys.update(d.keys())
        self.numeric_feature_names = sorted(list(all_keys))
        return self

    def _numeric_features(self, code: str) -> dict:
        nf = {}
        nf.update(ast_features(code))
        nf.update(surface_features(code))
        return nf

    def transform(self, codes: List[str]) -> np.ndarray:
        token_texts = [" ".join(tokenize_code(code)) for code in codes]
        X_tfidf = self.tfidf.transform(token_texts).toarray()
        X_num = []
        for code in codes:
            feats = self._numeric_features(code)
            X_num.append([feats.get(k, 0) for k in self.numeric_feature_names])
        X_num = np.array(X_num, dtype=float)
        return np.hstack([X_tfidf, X_num])

    def fit_transform(self, codes: List[str]) -> np.ndarray:
        self.fit(codes)
        return self.transform(codes)


# ------------------------
# 4. Train / Evaluate / Save / Demo
# ------------------------
def train_and_evaluate(snippets: List[str], labels: List[int], save_path="hdva_model.joblib"):
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(snippets, labels, test_size=0.2, random_state=42)
    fe = CodeFeatureExtractor(max_features_tfidf=800)
    print("Extracting features...")
    X_train = fe.fit_transform(X_train_raw)
    X_test = fe.transform(X_test_raw)

    clf = RandomForestClassifier(n_estimators=200, max_depth=16, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy: {acc:.4f}")
    print(classification_report(y_test, y_pred, target_names=["REAL", "HALLUCINATED"]))

    joblib.dump({"feature_extractor": fe, "model": clf}, save_path)
    print(f"Model saved to {save_path}")
    return acc


def load_model(path="hdva_model.joblib"):
    obj = joblib.load(path)
    return obj["feature_extractor"], obj["model"]


def demo_predict(example_snippets, fe, model):
    X = fe.transform(example_snippets)
    preds = model.predict(X)
    probs = model.predict_proba(X)[:, 1]
    for i, code in enumerate(example_snippets):
        print("\n" + "-" * 50)
        print(code.strip())
        print(f"Prediction: {'HALLUCINATED' if preds[i] == 1 else 'REAL'} (P={probs[i]:.3f})")


def main_demo():
    print("Generating synthetic dataset...")
    snippets, labels = synthetic_dataset(500, 500)
    acc = train_and_evaluate(snippets, labels)
    print(f"Demo complete. Synthetic accuracy ≈ {acc:.3f}")


# ------------------------
# 5. Command-line interface (NEW)
# ------------------------
if __name__ == "__main__":
    import argparse
    import os
    from pprint import pprint

    parser = argparse.ArgumentParser(description="HDVA Agent - Hallucination Detection & Validation")
    parser.add_argument("--file", type=str, help="Path to a Python file to analyze")
    parser.add_argument("--train", action="store_true", help="Train a new model on synthetic dataset")
    args = parser.parse_args()

    if args.train:
        main_demo()

    elif args.file:
        if not os.path.exists("hdva_model.joblib"):
            print("Model not found. Run with --train first.")
        else:
            fe, model = load_model("hdva_model.joblib")
            with open(args.file, "r", encoding="utf-8") as f:
                code = f.read()

            print(f"\nAnalyzing file: {args.file}")
            print("=" * 60)
            print(code[:300] + ("..." if len(code) > 300 else ""))

            feats = {}
            feats.update(ast_features(code))
            feats.update(surface_features(code))

            print("\n🧩 Extracted Features:")
            pprint(feats)

            X = fe.transform([code])
            pred = model.predict(X)[0]
            prob = model.predict_proba(X)[0][1]
            print("\n🤖 Prediction:")
            print(f"Result: {'HALLUCINATED' if pred == 1 else 'REAL'}")
            print(f"Confidence (P(hallucinated)) = {prob:.3f}")

    else:
        parser.print_help()
