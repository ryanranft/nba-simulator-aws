# Phase 5: Machine Learning Pipeline

**Status:** ✅ COMPLETE (📚 13 enhancement recommendations available)
**Priority:** MEDIUM-HIGH
**Prerequisites:** Phase 0-4 complete (simulations operational)
**Estimated Time:** 10-12 hours
**Cost Impact:** $50/month (SageMaker optional)
**Started:** October 3, 2025
**Completed:** October 3, 2025

> **📋 Note:** ML implementations reorganized into Phase 5 (October 18-26, 2025):
> - `5.0001_feature_engineering/` - Advanced temporal feature engineering (formerly `phase_0/rec_11`)
> - `5.0002_model_versioning/` - MLflow model lifecycle (formerly `phase_0/ml_systems_1`, renamed from 5.2_model_management)
> - `5.0019_drift_detection/` - Data drift detection (formerly `phase_0/ml_systems_2`)
> - `5.0020_panel_data/` - Temporal panel data processing (formerly `phase_0/rec_22`)
>
> All follow power directory structure with comprehensive README.md files.
> **Updated October 26, 2025:** All sub-phases standardized to 4-digit format (N.MMMM) per ADR-010.

---

## Overview

Build machine learning pipeline for game outcome prediction and player performance forecasting. This phase creates the ML infrastructure that boosts simulation accuracy from ~63% to target 75-80%.

**This phase delivers:**
- Feature engineering pipeline (temporal features)
- ML model training (Random Forest, XGBoost, Neural Networks)
- Model evaluation and validation
- Hyperparameter tuning
- Model deployment API
- Prediction accuracy tracking

**Why ML matters:**
- Boost win probability accuracy: 63% → 75-80%
- Enable player performance prediction
- Identify betting value opportunities
- Support what-if scenario analysis

---

## Sub-Phases

| Sub-Phase | Name | Status | Time | Documentation |
|-----------|------|--------|------|---------------|
| **5.0000** | ML Model Pipeline | ✅ COMPLETE ✓ | 10-12h | Oct 23, 2025 |
| **5.0001** | Feature Engineering | ✅ COMPLETE ✓ | ~6-8h | Oct 23, 2025 |
| **5.0002** | Model Versioning (MLflow) | ✅ COMPLETE ✓ | ~3h | Oct 23, 2025 |
| **5.0003** | Model Operations | 🔄 PARTIAL | - | [5.0003_model_operations/](phase_5/5.0003_model_operations/) |
| **5.0004** | Model Analysis | 🔄 PARTIAL | - | [5.0004_model_analysis/](phase_5/5.0004_model_analysis/) |
| **5.0005** | Experimentation | 🔄 PARTIAL | - | [5.0005_experimentation/](phase_5/5.0005_experimentation/) |
| **5.0006** | Hyperparameter Optimization | ✅ COMPLETE ✓ | ~2h | Oct 23, 2025 |
| **5.0007** | Model Interpretation | ✅ COMPLETE ✓ | ~2h | Oct 23, 2025 |
| **5.0008** | Feature Store | ✅ COMPLETE ✓ | ~2h | Oct 23, 2025 |
| **5.0009** | Automated Retraining | ✅ COMPLETE ✓ | ~2h | Oct 23, 2025 |
| **5.0010** | Feature Selection | ✅ COMPLETE ✓ | ~2h | Oct 23, 2025 |
| **5.0011** | Ensemble Learning | ✅ COMPLETE ✓ | ~2h | Oct 23, 2025 |
| **5.0012** | Learning Curves | ✅ COMPLETE ✓ | ~2h | Oct 23, 2025 |
| **5.0013** | Model Calibration | ✅ COMPLETE ✓ | ~2h | Oct 23, 2025 |
| **5.0014** | Cross-Validation Strategies | ✅ COMPLETE ✓ | ~2h | Oct 23, 2025 |
| **5.0015** | Model Comparison & Benchmarking | ✅ COMPLETE ✓ | ~2h | Oct 23, 2025 |
| **5.0016** | Error Analysis | ✅ COMPLETE ✓ | ~2h | Oct 23, 2025 |
| **5.0017** | Model Explainability | ✅ COMPLETE ✓ | ~2h | Oct 23, 2025 |
| **5.0018** | Performance Profiling | ✅ COMPLETE ✓ | ~2h | Oct 23, 2025 |
| **5.0019** | Drift Detection | ✅ COMPLETE ✓ | ~4h | Oct 23, 2025 |
| **5.0020** | Panel Data Processing | ✅ COMPLETE ✓ | ~6h | Oct 23, 2025 |
| **5.0021** | Model Performance Tracking | ✅ COMPLETE ✓ | ~6h | Oct 23, 2025 |
| **5.0022** | A/B Testing Framework | ✅ COMPLETE ✓ | ~4h | Oct 23, 2025 |
| **5.0023** | Advanced ML Pipeline | ✅ COMPLETE ✓ | ~6h | Oct 23, 2025 |
| **5.0024** | Performance Optimization | ✅ COMPLETE ✓ | ~4h | Oct 23, 2025 |
| **5.0025** | Realtime Prediction Engine | ✅ COMPLETE ✓ | ~4h | Oct 23, 2025 |
| **5.0026** | ML Feedback Loop | ✅ COMPLETE ✓ | ~3h | Oct 23, 2025 |

**Total Sub-Phases:** 195 (27 core ML frameworks + 168 book recommendations)
**Note:** Phase 5 expanded through reorganization and book recommendations:
- 5.0001, 5.0002 migrated from phase_0 (October 18, 2025)
- 5.0019, 5.0020 migrated from phase_0 (October 18, 2025)
- 5.0021-5.0026 added from autonomous book recommendations (October 19, 2025)
- 5.0027-5.0169: Book recommendations (implemented October 19, 2025)
- **5.0170-5.0195:** Duplicate resolution (October 26, 2025) - Book recommendations originally numbered 5.1-5.26 renumbered to avoid conflicts with ML frameworks
- **4-digit format:** All sub-phases standardized to N.MMMM format (October 26, 2025) per ADR-010
**Total Implementation Time:** ~85 hours (core frameworks)
**Source:** MCP Book Recommendations + Econometric/ML technical books

---

## Book Recommendations

**Status:** Available for implementation
**Source:** AI/ML technical book analysis (20 books)
**Total Recommendations:** 13 recommendations for this phase

This phase has 13 recommendations from technical book analysis:
- Critical: 5 recommendations
- Important: 4 recommendations
- Nice-to-Have: 4 recommendations

**See:** [Book Recommendations](phase_5/RECOMMENDATIONS_FROM_BOOKS.md) for complete details

**Proposed Updates:** [Proposed Updates](phase_5/PROPOSED_UPDATES.md) for integration analysis

---

## Sub-Phase 5.0: ML Model Pipeline

**Status:** ✅ COMPLETE (October 3, 2025)

**What was completed:**
- Feature engineering pipeline (temporal features)
- ML model training (Random Forest, XGBoost)
- Cross-validation framework
- Model evaluation metrics
- Hyperparameter tuning (GridSearchCV)
- Model serialization and deployment
- Prediction API

**Models Trained:**
1. **Random Forest:** Baseline model (accuracy ~70%)
2. **XGBoost:** Gradient boosting (accuracy ~75%)
3. **Neural Network:** Deep learning (experimental, ~72%)

**Feature Categories:**
- Temporal features: Cumulative stats at exact timestamps
- Momentum features: Recent performance trends
- Contextual features: Home/away, rest days, back-to-back
- Player interaction features: Lineup combinations

**Best Model:** XGBoost with 75% accuracy (vs 63% baseline)

**See:** [Sub-Phase 5.0 Details](phase_5/5.0_machine_learning_models.md)

---

## Success Criteria

- [x] Feature engineering pipeline operational
- [x] Multiple models trained and evaluated
- [x] Cross-validation implemented
- [x] Hyperparameter tuning complete
- [x] Model accuracy > 70% (achieved 75%)
- [x] Models serialized and deployable
- [x] Prediction API working
- [x] Documentation complete

---

## Cost Breakdown

| Resource | Configuration | Monthly Cost | Notes |
|----------|--------------|--------------|-------|
| Local training | Free (CPU/GPU) | $0 | Sufficient for development |
| SageMaker (optional) | ml.m5.xlarge | $50/month | For large-scale training |
| S3 model storage | <1GB | ~$0.02/month | Model artifacts |
| **Total Phase Cost** | | **$0-50/month** | Depends on training volume |

**Cost Optimization:**
- Train locally for development (free)
- Use SageMaker only for production model training
- Cache feature engineering results to avoid recomputation

---

## Prerequisites

**Before starting Phase 5:**
- [x] Phase 0-4 complete (simulation engine operational)
- [x] Temporal features available in database
- [ ] Python ML libraries (scikit-learn, XGBoost, TensorFlow)
- [ ] Training data prepared (labeled historical games)

---

## Key Architecture Decisions

**ADRs created in Phase 5:**
- XGBoost over Random Forest (better accuracy)
- Local training over SageMaker (cost optimization)
- Feature engineering focused on temporal patterns

**See:** `docs/adr/README.md`

---

## Feature Engineering

**Temporal features extracted:**
1. **Cumulative stats at timestamp:** Points, rebounds, assists up to exact moment
2. **Momentum indicators:** Last 5 games, last 10 minutes, hot/cold streaks
3. **Contextual variables:** Home/away, rest days, injuries, matchups
4. **Player interactions:** Lineup net rating, +/- combinations
5. **Derived metrics:** PER, TS%, usage rate, win shares

**Total features:** 150-200 depending on data availability

**See:** `docs/ML_FEATURE_CATALOG.md` for complete feature breakdown

---

## Model Performance

### Baseline (Monte Carlo only)
- **Accuracy:** 63%
- **Method:** Probabilistic simulation, no ML

### Random Forest
- **Accuracy:** 70%
- **Training time:** ~30 minutes
- **Pros:** Interpretable, fast
- **Cons:** Prone to overfitting

### XGBoost (Best Model)
- **Accuracy:** 75%
- **Training time:** ~45 minutes
- **Pros:** Best performance, handles missing data
- **Cons:** Longer training, less interpretable

### Neural Network (Experimental)
- **Accuracy:** 72%
- **Training time:** ~2 hours
- **Pros:** Flexible, can capture complex patterns
- **Cons:** Requires more data, overfits easily

**Target:** 75-80% accuracy (achieved 75% with XGBoost)

---

## Multi-Sport Replication

**When adding a new sport (NFL, MLB, NHL, Soccer):**

This phase is **mostly sport-agnostic** - ML pipeline is reusable:

**Reusable components:**
- Feature engineering framework
- Model training pipeline
- Hyperparameter tuning workflow
- Model evaluation metrics

**Sport-specific adaptations:**
- Feature definitions (sport-specific stats)
- Outcome variable (win/loss, score differential)
- Feature importance ranking (different factors matter per sport)

**Example for NFL:**
```python
# NFL-specific features
features = [
    'passing_yards_cumulative',
    'rushing_yards_cumulative',
    'turnovers',
    'time_of_possession',
    'third_down_conversion_rate',
    # ... NFL-specific temporal features
]
```

---

## Key Workflows

**For Sub-Phase 5.0:**
- Workflow #13: Testing Framework
- Workflow #5: Task Execution
- Workflow #2: Command Logging

---

## Troubleshooting

**Common issues:**

1. **Model overfitting (high train, low test accuracy)**
   - Solution: Increase regularization
   - Reduce model complexity
   - Get more training data

2. **Feature engineering slow**
   - Solution: Cache computed features
   - Use materialized views in database
   - Parallelize feature computation

3. **Low model accuracy**
   - Solution: Add more features (Phase 1 multi-source)
   - Try different model architectures
   - Tune hyperparameters more aggressively

4. **Training takes too long**
   - Solution: Reduce training data size (sample)
   - Use faster models (Random Forest over Neural Net)
   - Consider distributed training (SageMaker)

---

## Next Steps

**After Phase 5 complete:**
- ✅ ML pipeline operational
- ✅ Models trained and deployed
- → Proceed to [Phase 6: Optional Enhancements](PHASE_6_INDEX.md)
- → Optional: [Phase 7: Betting Odds Integration](PHASE_7_INDEX.md)

---

## Navigation

**Return to:** [PROGRESS.md](../../PROGRESS.md)
**Previous Phase:** [Phase 4: Simulation Engine](PHASE_4_INDEX.md)
**Next Phase:** [Phase 6: Optional Enhancements](PHASE_6_INDEX.md)
**Workflow Index:** [CLAUDE_WORKFLOW_ORDER.md](../claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

**Related Documentation:**
- [ML Feature Catalog](../ML_FEATURE_CATALOG.md) (209 features across all sources)
- [Model Performance Tracking](../MODEL_PERFORMANCE.md)
- [Feature Engineering Guide](../FEATURE_ENGINEERING_GUIDE.md)

---

*For Claude Code: This phase has a single sub-phase. ML pipeline is operational and models are trained.*

---

**Last Updated:** October 18, 2025
**Phase Owner:** ML Team
**Total Sub-Phases:** 27 (5.0 + 5.1-5.26 from MCP recommendations + book analysis)
**Status:** 100% complete (27 of 27 sub-phases done)


## Enhancement: Add model drift detection alerts

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:34:43.596576
**Category:** important

### Description
No additional description provided.

### Implementation Notes
- This enhancement was automatically added based on book analysis
- Review and adjust implementation details as needed
- Consider impact on existing phase timeline

---


## Enhancement: Add interactive documentation

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:34:43.596884
**Category:** nice_to_have

### Description
No additional description provided.

### Implementation Notes
- This enhancement was automatically added based on book analysis
- Review and adjust implementation details as needed
- Consider impact on existing phase timeline

---


## Enhancement: Add code examples for edge cases

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:34:43.597010
**Category:** nice_to_have

### Description
No additional description provided.

### Implementation Notes
- This enhancement was automatically added based on book analysis
- Review and adjust implementation details as needed
- Consider impact on existing phase timeline

---


## New Item: Implement model registry with versioning

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:34:43.597191
**Category:** critical
**Priority:** Critical

### Description
No additional description provided.

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: Implement feature importance tracking

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:34:43.597366
**Category:** important
**Priority:** Important

### Description
No additional description provided.

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: Improve inline documentation

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:34:43.597534
**Category:** nice_to_have
**Priority:** Nice_To_Have

### Description
No additional description provided.

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: Implement A/B testing statistical framework

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:34:43.597704
**Category:** important
**Priority:** Important

### Description
No additional description provided.

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## Enhancement: Add model drift detection alerts

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:41:44.914812
**Category:** important

### Description
No additional description provided.

### Implementation Notes
- This enhancement was automatically added based on book analysis
- Review and adjust implementation details as needed
- Consider impact on existing phase timeline

---


## Enhancement: Add interactive documentation

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:41:44.915189
**Category:** nice_to_have

### Description
No additional description provided.

### Implementation Notes
- This enhancement was automatically added based on book analysis
- Review and adjust implementation details as needed
- Consider impact on existing phase timeline

---


## Enhancement: Add code examples for edge cases

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:41:44.915410
**Category:** nice_to_have

### Description
No additional description provided.

### Implementation Notes
- This enhancement was automatically added based on book analysis
- Review and adjust implementation details as needed
- Consider impact on existing phase timeline

---


## New Item: Implement model registry with versioning

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:41:44.915597
**Category:** critical
**Priority:** Critical

### Description
No additional description provided.

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: Implement feature importance tracking

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:41:44.915778
**Category:** important
**Priority:** Important

### Description
No additional description provided.

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: Improve inline documentation

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:41:44.915920
**Category:** nice_to_have
**Priority:** Nice_To_Have

### Description
No additional description provided.

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: Implement A/B testing statistical framework

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:41:44.916041
**Category:** important
**Priority:** Important

### Description
No additional description provided.

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: Model Versioning with MLflow

**Source:** Designing Machine Learning Systems
**Date Added:** 2025-10-12T14:43:24.691810
**Category:** critical
**Priority:** Critical

### Description
From ML Systems book: Ch 5, Ch 10

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: Automated Retraining Pipeline

**Source:** Designing Machine Learning Systems
**Date Added:** 2025-10-12T14:43:24.691972
**Category:** critical
**Priority:** Critical

### Description
From ML Systems book: Ch 9, Ch 10

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: Feature Store

**Source:** Designing Machine Learning Systems
**Date Added:** 2025-10-12T14:43:24.692094
**Category:** important
**Priority:** Important

### Description
From ML Systems book: Ch 5

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: A/B Testing Framework

**Source:** Designing Machine Learning Systems
**Date Added:** 2025-10-12T14:43:24.692215
**Category:** important
**Priority:** Important

### Description
From ML Systems book: Ch 7

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: Model Explainability (SHAP)

**Source:** Designing Machine Learning Systems
**Date Added:** 2025-10-12T14:43:24.692332
**Category:** nice_to_have
**Priority:** Nice_To_Have

### Description
From ML Systems book: Ch 6, Ch 11

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: Feedback Loop

**Source:** Designing Machine Learning Systems
**Date Added:** 2025-10-12T14:43:24.692444
**Category:** nice_to_have
**Priority:** Nice_To_Have

### Description
From ML Systems book: Ch 9

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: Model Registry

**Source:** Designing Machine Learning Systems
**Date Added:** 2025-10-12T14:43:24.692742
**Category:** nice_to_have
**Priority:** Nice_To_Have

### Description
From ML Systems book: Ch 5, Ch 10

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## How Phase 5 Enables the Simulation Vision

This phase provides [data/infrastructure/capability] that powers the **hybrid econometric + nonparametric simulation system** described in the [main README](../../README.md#simulation-methodology).

**What this phase enables:**

### 1. Econometric Causal Inference
From this phase's outputs, we can:
- [Specific econometric technique enabled]
- [Example: PPP estimation using panel data regression]

### 2. Nonparametric Event Modeling
From this phase's data, we build:
- [Specific nonparametric technique enabled]
- [Example: Kernel density estimation for technical fouls]

### 3. Context-Adaptive Simulations
Using this phase's data, simulations can adapt to:
- [Game situation context]
- [Player/team specific factors]

**See [main README](../../README.md) for complete methodology.**
