# Explainable hybrid risk scoring

## Purpose

Phase 3 ranks synthetic payment events for analyst attention. It is a challenge-demo decision-support engine, not a live fraud-control system.

## Components

| Component | Weight | What it captures |
| --- | ---: | --- |
| Logistic ML probability | 65% | Learnable relationship across transaction amount, velocity, failures, device novelty, country novelty, and failure status |
| Behavioral rules | 25% | High-confidence, easily audited policy signals |
| Anomaly signal | 10% | Amount deviation plus new-device and unusual-country novelty |

## Explainability payload

Every `POST /api/v1/transactions/{id}/assessments` response and persisted assessment includes:

- overall score and recommended decision;
- ML probability, rules score, and anomaly score;
- model version used;
- engineered values, including customer median-relative amount, ten-minute velocity, and 24-hour failure count;
- reason strings describing triggered rules.

## Model training boundary

`POST /api/v1/models/train` uses synthetic labels only. The baseline learns with batch gradient descent and stores weights plus provenance. This allows the demo to show an actual train/infer/version/audit lifecycle without overstating the validity of synthetic performance.

## Next improvements

Phase 4 should add labeled outcome feedback and calibration/evaluation metrics. Phase 5 should let the investigation agent read these stored explanations rather than infer unsupported facts.
