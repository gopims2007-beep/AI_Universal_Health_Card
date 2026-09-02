import argparse
from pathlib import Path
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.linear_model import LogisticRegression

def main():
    parser = argparse.ArgumentParser(description="Train a real disease-risk classifier from a supplied dataset.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    if args.target not in df.columns:
        raise SystemExit(f"Target column '{args.target}' not found. Columns: {list(df.columns)}")
    if len(df) < 20:
        raise SystemExit("Dataset is too small for a meaningful training run. Supply a real dataset with sufficient records.")

    X = df.drop(columns=[args.target])
    y = df[args.target].astype(str)
    if y.nunique() < 2:
        raise SystemExit("Target must contain at least two classes.")

    numeric = X.select_dtypes(include=["number"]).columns.tolist()
    categorical = [c for c in X.columns if c not in numeric]

    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("imputer", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical))

    pre = ColumnTransformer(transformers)
    model = Pipeline([
        ("preprocessor", pre),
        ("classifier", LogisticRegression(max_iter=2000)),
    ])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    print(classification_report(y_test, pred))

    out = Path(__file__).resolve().parent / "models"
    out.mkdir(exist_ok=True)
    joblib.dump(model, out / "disease_risk.joblib")
    print(f"Saved trained model to {out / 'disease_risk.joblib'}")

if __name__ == "__main__":
    main()
