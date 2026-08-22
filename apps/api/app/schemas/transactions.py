from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

PaymentMethod = Literal["card", "upi", "netbanking", "wallet"]
TransactionStatus = Literal["authorized", "captured", "failed", "refunded"]


class TransactionCreate(BaseModel):
    external_reference: str | None = Field(default=None, max_length=100)
    customer_id: str = Field(min_length=1, max_length=100)
    payment_token: str = Field(min_length=8, max_length=128)
    amount_paise: int = Field(gt=0, le=100_000_000)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    payment_method: PaymentMethod
    merchant_category: str = Field(min_length=1, max_length=80)
    status: TransactionStatus
    occurred_at: datetime
    device_id: str | None = Field(default=None, max_length=128)
    ip_hash: str | None = Field(default=None, max_length=128)
    country_code: str = Field(default="IN", min_length=2, max_length=2)
    city: str | None = Field(default=None, max_length=80)
    context: dict[str, Any] | None = None


class TransactionRead(TransactionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime


class TransactionList(BaseModel):
    items: list[TransactionRead]
    limit: int
    offset: int
    total: int
