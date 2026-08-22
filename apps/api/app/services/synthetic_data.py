"""Deterministic synthetic data generation for demos and local development."""

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from random import Random

from app.schemas.transactions import TransactionCreate

MERCHANT_CATEGORIES = ("grocery", "electronics", "travel", "food_delivery", "fashion")
CITIES = (("IN", "Bengaluru"), ("IN", "Mumbai"), ("IN", "Delhi"), ("IN", "Pune"))
PAYMENT_METHODS = ("card", "upi", "netbanking", "wallet")


def _hash(value: str) -> str:
    return sha256(value.encode()).hexdigest()[:32]


def generate_transactions(count: int, seed: int = 42) -> list[TransactionCreate]:
    """Return representative, non-identifying payment events with reproducible randomness."""
    random = Random(seed)
    now = datetime.now(UTC).replace(microsecond=0)
    transactions: list[TransactionCreate] = []
    for index in range(count):
        customer_number = random.randint(1, max(3, count // 4))
        country_code, city = random.choice(CITIES)
        customer_id = f"cust_demo_{customer_number:04d}"
        device_id = f"device_demo_{random.randint(1, max(5, count // 3)):04d}"
        occurred_at = now - timedelta(minutes=random.randint(0, 60 * 24 * 30))
        transactions.append(
            TransactionCreate(
                external_reference=f"demo_txn_{index + 1:05d}",
                customer_id=customer_id,
        payment_token=f"tok_demo_{_hash(f'{seed}:{index}')}",
        amount_paise=random.choice((9900, 19900, 49900, 99900, 249900)),
        payment_method=random.choice(PAYMENT_METHODS),  # type: ignore[arg-type]
        merchant_category=random.choice(MERCHANT_CATEGORIES),
        status=random.choices(
            ("captured", "failed", "authorized"),
            weights=(82, 12, 6),
        )[0],
        occurred_at=occurred_at,
        device_id=device_id,
        ip_hash=_hash(f"ip:{random.randint(1, 30)}"),
        country_code=country_code,
        city=city,
        context={"source": "synthetic", "generator_version": "1"},
    )
        )
    return transactions
