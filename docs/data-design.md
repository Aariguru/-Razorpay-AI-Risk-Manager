# Data design and privacy boundary

## Transaction record

The Phase 2 `transactions` table holds a tokenized payment event suitable for simulated risk analysis.

| Field | Purpose | Safety boundary |
| --- | --- | --- |
| `id` | Internal UUID | System-generated |
| `external_reference` | Idempotency/demo reference | Synthetic identifier |
| `customer_id` | Customer behavior aggregation key | Pseudonymous identifier |
| `payment_token` | Payment-instrument surrogate | Token only; never a PAN |
| `amount_paise`, `currency` | Transaction value | Required for risk features |
| `payment_method`, `merchant_category`, `status` | Payment context | Controlled values |
| `occurred_at` | Event time | Enables velocity features |
| `device_id`, `ip_hash` | Device/network surrogate | Hashed/tokenized only |
| `country_code`, `city` | Coarse location context | Synthetic demo values |
| `context` | Extensible, non-sensitive metadata | Must not contain secrets or card data |

## Explicitly prohibited data

The API deliberately has no fields for primary account numbers (PANs), CVVs, PINs, bank credentials, access tokens, or real Razorpay customer data. Unknown request fields are ignored by Pydantic's default compatibility behavior, but they must never be added to the persistence model.

## Synthetic generator

`apps/api/scripts/generate_synthetic_data.py` produces deterministic JSONL with a seed. It models ordinary payment variety—customers, devices, amounts, payment methods, merchant categories, and failures—without representing real people or payment instruments. Phase 3 will add labeled suspicious-pattern scenarios for model training and evaluation.
