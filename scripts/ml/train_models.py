#!/usr/bin/env python3
"""
NBA Game Prediction - Model Training Script
Trains baseline and advanced ML models for game outcome prediction
"""

import pandas as pd
import numpy as np
import pickle
import boto3
from io import BytesIO
from datetime import datetime
import os
import sys

# Scikit-learn
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix,
    classification_report
)

# Advanced models
import xgboost as xgb
import lightgbm as lgb

# S3 configuration
S3_BUCKET = 'nba-sim-raw-data-lake'
S3_FEATURES_PREFIX = 'ml-features'
S3_MODELS_PREFIX = 'ml-models'

def main():
    print("=" * 70)
    print("NBA GAME PREDICTION - MODEL TRAINING")
    print("=" * 70)
    print()

    # 1. Load data from S3
    print("[1/6] Loading feature data from S3...")
    train_df = pd.read_parquet(f's3://{S3_BUCKET}/{S3_FEATURES_PREFIX}/train.parquet')
    test_df = pd.read_parquet(f's3://{S3_BUCKET}/{S3_FEATURES_PREFIX}/test.parquet')

    # Prepare features and target
    id_cols = ['game_id', 'game_date', 'season', 'home_team_id', 'away_team_id']
    target_col = 'home_win'
    feature_cols = [col for col in train_df.columns if col not in id_cols + [target_col]]

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    print(f"✓ Data loaded")
    print(f"  Train: {X_train.shape[0]:,} games, {X_train.shape[1]} features")
    print(f"  Test:  {X_test.shape[0]:,} games, {X_test.shape[1]} features")
    print(f"  Features: {', '.join(feature_cols[:5])}...")

    # 2. Scale features
    print("\n[2/6] Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print("✓ Features scaled")

    # Store results
    results = {}
    models = {}

    # 3. Train Logistic Regression
    print("\n[3/6] Training Logistic Regression...")
    lr_model = LogisticRegression(random_state=42, max_iter=1000)
    lr_model.fit(X_train_scaled, y_train)

    y_train_pred_lr = lr_model.predict(X_train_scaled)
    y_test_pred_lr = lr_model.predict(X_test_scaled)
    y_test_proba_lr = lr_model.predict_proba(X_test_scaled)[:, 1]

    results['Logistic Regression'] = {
        'train_acc': accuracy_score(y_train, y_train_pred_lr),
        'test_acc': accuracy_score(y_test, y_test_pred_lr),
        'test_auc': roc_auc_score(y_test, y_test_proba_lr),
        'precision': precision_score(y_test, y_test_pred_lr),
        'recall': recall_score(y_test, y_test_pred_lr),
        'f1': f1_score(y_test, y_test_pred_lr)
    }
    models['Logistic Regression'] = lr_model

    print(f"✓ Logistic Regression trained")
    print(f"  Train Accuracy: {results['Logistic Regression']['train_acc']:.4f}")
    print(f"  Test Accuracy:  {results['Logistic Regression']['test_acc']:.4f}")
    print(f"  Test AUC:       {results['Logistic Regression']['test_auc']:.4f}")

    # 4. Train Random Forest
    print("\n[4/6] Training Random Forest...")
    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=20,
        min_samples_leaf=10,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)

    y_train_pred_rf = rf_model.predict(X_train)
    y_test_pred_rf = rf_model.predict(X_test)
    y_test_proba_rf = rf_model.predict_proba(X_test)[:, 1]

    results['Random Forest'] = {
        'train_acc': accuracy_score(y_train, y_train_pred_rf),
        'test_acc': accuracy_score(y_test, y_test_pred_rf),
        'test_auc': roc_auc_score(y_test, y_test_proba_rf),
        'precision': precision_score(y_test, y_test_pred_rf),
        'recall': recall_score(y_test, y_test_pred_rf),
        'f1': f1_score(y_test, y_test_pred_rf)
    }
    models['Random Forest'] = rf_model

    print(f"✓ Random Forest trained")
    print(f"  Train Accuracy: {results['Random Forest']['train_acc']:.4f}")
    print(f"  Test Accuracy:  {results['Random Forest']['test_acc']:.4f}")
    print(f"  Test AUC:       {results['Random Forest']['test_auc']:.4f}")

    # 5. Train XGBoost
    print("\n[5/6] Training XGBoost...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        eval_metric='logloss'
    )
    xgb_model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_train_pred_xgb = xgb_model.predict(X_train)
    y_test_pred_xgb = xgb_model.predict(X_test)
    y_test_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]

    results['XGBoost'] = {
        'train_acc': accuracy_score(y_train, y_train_pred_xgb),
        'test_acc': accuracy_score(y_test, y_test_pred_xgb),
        'test_auc': roc_auc_score(y_test, y_test_proba_xgb),
        'precision': precision_score(y_test, y_test_pred_xgb),
        'recall': recall_score(y_test, y_test_pred_xgb),
        'f1': f1_score(y_test, y_test_pred_xgb)
    }
    models['XGBoost'] = xgb_model

    print(f"✓ XGBoost trained")
    print(f"  Train Accuracy: {results['XGBoost']['train_acc']:.4f}")
    print(f"  Test Accuracy:  {results['XGBoost']['test_acc']:.4f}")
    print(f"  Test AUC:       {results['XGBoost']['test_auc']:.4f}")

    # 6. Train LightGBM
    print("\n[6/6] Training LightGBM...")
    lgb_model = lgb.LGBMClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        num_leaves=31,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    lgb_model.fit(X_train, y_train, eval_set=[(X_test, y_test)])

    y_train_pred_lgb = lgb_model.predict(X_train)
    y_test_pred_lgb = lgb_model.predict(X_test)
    y_test_proba_lgb = lgb_model.predict_proba(X_test)[:, 1]

    results['LightGBM'] = {
        'train_acc': accuracy_score(y_train, y_train_pred_lgb),
        'test_acc': accuracy_score(y_test, y_test_pred_lgb),
        'test_auc': roc_auc_score(y_test, y_test_proba_lgb),
        'precision': precision_score(y_test, y_test_pred_lgb),
        'recall': recall_score(y_test, y_test_pred_lgb),
        'f1': f1_score(y_test, y_test_pred_lgb)
    }
    models['LightGBM'] = lgb_model

    print(f"✓ LightGBM trained")
    print(f"  Train Accuracy: {results['LightGBM']['train_acc']:.4f}")
    print(f"  Test Accuracy:  {results['LightGBM']['test_acc']:.4f}")
    print(f"  Test AUC:       {results['LightGBM']['test_auc']:.4f}")

    # 7. Compare models
    print("\n" + "=" * 70)
    print("MODEL COMPARISON")
    print("=" * 70)

    comparison_df = pd.DataFrame(results).T
    comparison_df = comparison_df.sort_values('test_auc', ascending=False)

    print("\nPerformance Summary:")
    print(comparison_df.to_string(float_format=lambda x: f'{x:.4f}'))

    best_model_name = comparison_df.index[0]
    best_model = models[best_model_name]
    best_auc = comparison_df.loc[best_model_name, 'test_auc']

    print(f"\n🏆 Best Model: {best_model_name} (AUC: {best_auc:.4f})")

    # 8. Save models to S3
    print(f"\n[8/8] Saving models to S3...")
    s3 = boto3.client('s3')

    for model_name, model in models.items():
        # Save model
        model_buffer = BytesIO()
        pickle.dump(model, model_buffer)
        model_buffer.seek(0)

        model_key = f"{S3_MODELS_PREFIX}/{model_name.lower().replace(' ', '_')}.pkl"
        s3.put_object(Bucket=S3_BUCKET, Key=model_key, Body=model_buffer.getvalue())
        print(f"  ✓ Saved {model_name} to s3://{S3_BUCKET}/{model_key}")

    # Save scaler
    scaler_buffer = BytesIO()
    pickle.dump(scaler, scaler_buffer)
    scaler_buffer.seek(0)
    scaler_key = f"{S3_MODELS_PREFIX}/scaler.pkl"
    s3.put_object(Bucket=S3_BUCKET, Key=scaler_key, Body=scaler_buffer.getvalue())
    print(f"  ✓ Saved scaler to s3://{S3_BUCKET}/{scaler_key}")

    # Save results
    results_df = pd.DataFrame(results).T
    results_buffer = BytesIO()
    results_df.to_csv(results_buffer, index=True)
    results_buffer.seek(0)
    results_key = f"{S3_MODELS_PREFIX}/model_results.csv"
    s3.put_object(Bucket=S3_BUCKET, Key=results_key, Body=results_buffer.getvalue())
    print(f"  ✓ Saved results to s3://{S3_BUCKET}/{results_key}")

    # Summary
    print("\n" + "=" * 70)
    print("MODEL TRAINING COMPLETE")
    print("=" * 70)
    print(f"\n📊 Models Trained: {len(models)}")
    print(f"  1. Logistic Regression (baseline)")
    print(f"  2. Random Forest")
    print(f"  3. XGBoost")
    print(f"  4. LightGBM")

    print(f"\n📈 Best Performance:")
    print(f"  Model: {best_model_name}")
    print(f"  Test Accuracy: {comparison_df.loc[best_model_name, 'test_acc']:.1%}")
    print(f"  Test AUC: {best_auc:.3f}")
    print(f"  Precision: {comparison_df.loc[best_model_name, 'precision']:.3f}")
    print(f"  Recall: {comparison_df.loc[best_model_name, 'recall']:.3f}")
    print(f"  F1 Score: {comparison_df.loc[best_model_name, 'f1']:.3f}")

    goal_met = comparison_df.loc[best_model_name, 'test_acc'] > 0.60
    print(f"\n{'✓' if goal_met else '⚠️ '} Goal {'achieved' if goal_met else 'not met'}: Accuracy > 60%")

    print(f"\n💾 S3 Outputs:")
    print(f"  Models: s3://{S3_BUCKET}/{S3_MODELS_PREFIX}/")
    print(f"  Results: s3://{S3_BUCKET}/{S3_MODELS_PREFIX}/model_results.csv")

    print(f"\n🎯 Next Steps:")
    print(f"  1. Review model performance and feature importance")
    print(f"  2. Consider hyperparameter tuning for best model")
    print(f"  3. Deploy best model for predictions")
    print("=" * 70)

if __name__ == '__main__':
    main()