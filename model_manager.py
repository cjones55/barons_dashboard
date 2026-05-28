#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 00:12:59 2026

@author: chrisjones
"""

# model_manager.py

import os
import joblib
import pandas as pd
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.impute import SimpleImputer

from data_loader import load_statcast_2024


# ============================
# 1. Directory for saved models
# ============================

def get_model_dir():
    desktop = Path.home() / "Desktop"
    model_dir = desktop / "stuff_models"
    model_dir.mkdir(exist_ok=True)
    return model_dir


# ============================
# 2. Train a model for one pitch type
# ============================

def train_pitch_type_model(df, pitch_type):
    d = df[df["pitch_type"] == pitch_type].copy()

    if len(d) < 500:
        print(f"Skipping {pitch_type}: not enough samples ({len(d)})")
        return None, None

    # -------------------------
    # Feature lists
    # -------------------------
    num_features = [
        "velo_diff", "spin_diff", "hb_diff", "ivb_diff",
        "vaa", "gyro_deg", "velo_sep",
        "tunnel_dist", "tunnel_ext_diff",
        "plate_x", "plate_z",
        "release_pos_x", "release_pos_z", "release_extension",
        "balls", "strikes", "pitch_number"
    ]

    cat_features = ["stand", "p_throws"]

    X = d[num_features + cat_features]
    y = d["whiff"]

    # -------------------------
    # IMPUTATION + ENCODING
    # -------------------------
    preprocess = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median"), num_features),
            ("cat", Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore"))
            ]), cat_features),
        ]
    )

    # -------------------------
    # Model
    # -------------------------
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        n_jobs=-1,
        random_state=42
    )

    clf = Pipeline(steps=[
        ("preprocess", preprocess),
        ("model", model)
    ])

    # -------------------------
    # Train/test split
    # -------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # -------------------------
    # Fit model
    # -------------------------
    clf.fit(X_train, y_train)

    # -------------------------
    # Evaluate
    # -------------------------
    auc = roc_auc_score(y_test, clf.predict_proba(X_test)[:, 1])
    print(f"{pitch_type} model trained — ROC-AUC: {auc:.3f}")

    return clf, auc


# ============================
# 3. Save a trained model
# ============================

def save_model(clf, pitch_type):
    model_dir = get_model_dir()
    path = model_dir / f"{pitch_type}_model.pkl"
    joblib.dump(clf, path)
    print(f"Saved model: {path}")


# ============================
# 4. Load a trained model
# ============================

def load_model(pitch_type):
    model_dir = get_model_dir()
    path = model_dir / f"{pitch_type}_model.pkl"

    if not path.exists():
        raise FileNotFoundError(f"No saved model found for pitch type {pitch_type}")

    return joblib.load(path)


# ============================
# 5. Predict whiff probability for a pitch type
# ============================

def predict_pitch_type(df, pitch_type):
    clf = load_model(pitch_type)

    num_features = [
        "velo_diff", "spin_diff", "hb_diff", "ivb_diff",
        "vaa", "gyro_deg", "velo_sep",
        "tunnel_dist", "tunnel_ext_diff",
        "plate_x", "plate_z",
        "release_pos_x", "release_pos_z", "release_extension",
        "balls", "strikes", "pitch_number"
    ]

    cat_features = ["stand", "p_throws"]

    d = df[df["pitch_type"] == pitch_type]
    X = d[num_features + cat_features]

    preds = clf.predict_proba(X)[:, 1]
    return preds


# ============================
# 6. Train ALL pitch-type models
# ============================

def train_all_models():
    df = load_statcast_2024()

    pitch_types = sorted(df["pitch_type"].unique())

    results = []

    for pt in pitch_types:
        clf, auc = train_pitch_type_model(df, pt)

        if clf is not None:
            save_model(clf, pt)
            results.append((pt, auc))

    print("\n=== Training Complete ===")
    for pt, auc in results:
        print(f"{pt}: AUC {auc:.3f}")


# ============================
# 7. Run training if executed directly
# ============================

if __name__ == "__main__":
    train_all_models()
 