"""Pydantic v2 request/response schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None = None
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SubscriptionCreate(BaseModel):
    merchant: str
    plan_name: str
    category: str | None = None
    price_monthly_usd: float = Field(gt=0)
    started_on: str | None = None
    next_billing_on: str | None = None
    last_used_days_ago: int = Field(ge=0)
    paypal_subscription_id: str | None = None


class SubscriptionUpdate(BaseModel):
    merchant: str | None = None
    plan_name: str | None = None
    category: str | None = None
    price_monthly_usd: float | None = Field(default=None, gt=0)
    started_on: str | None = None
    next_billing_on: str | None = None
    last_used_days_ago: int | None = Field(default=None, ge=0)
    paypal_subscription_id: str | None = None
    status: str | None = None


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    merchant: str | None = None
    plan_name: str | None = None
    category: str | None = None
    price_monthly_usd: float | None = None
    currency: str = "USD"
    status: str = "ACTIVE"
    paypal_subscription_id: str | None = None
    started_on: str | None = None
    next_billing_on: str | None = None
    last_used_days_ago: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ApproveRequest(BaseModel):
    subscription_ids: list[str]


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    body: str | None = None
    is_read: bool = False
    created_at: datetime | None = None


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    detail: str | None = None
    created_at: datetime | None = None


class AdminStats(BaseModel):
    total_users: int
    total_subscriptions: int
    active_subscriptions: int
    cancelled_subscriptions: int
    total_monthly_usd: float
