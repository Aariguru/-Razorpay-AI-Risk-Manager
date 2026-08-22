# Model card (placeholder)

## Current baseline

The first runnable model is a logistic regression trained by gradient descent on reproducible labeled synthetic feature vectors. Training is exposed through `POST /api/v1/models/train`; each generated parameter set is versioned in `model_versions`.

## Intended use

Prioritize synthetic payment events for allow, review, or block recommendations in a challenge demonstration. It is not intended for live financial decisions.

## Planned model family

A synthetic logistic-regression baseline, with a calibrated logistic-regression or gradient-boosting comparison planned after real public/synthetic evaluation data is available. The deployed score combines ML, deterministic rules, and anomaly signals.

## Planned evaluation

PR-AUC, recall at review capacity, precision, calibration, false-positive rate, score latency, and decision/override rates. The current training endpoint stores its sample count and synthetic label source, not production-quality performance claims.

## Constraints

Training and demo data will be synthetic or public. No raw card data, private Razorpay data, or unsupported demographic inference will be used.

## Score composition

`risk_score = 100 × (0.65 × ML probability + 0.25 × rules score + 0.10 × anomaly score)`

Scores are rounded to 0–100 and map to `allow` (<35), `manual_review` (35–69), or `block` (70+). Each assessment stores its components, engineered features, human-readable triggered reasons, and model version.
