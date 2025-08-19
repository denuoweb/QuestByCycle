"""Pydantic schemas for request validation."""
from __future__ import annotations

from typing import Any, Dict, Optional, Literal

from pydantic import BaseModel, constr, conint


class SubscriptionKeysSchema(BaseModel):
    p256dh: constr(min_length=1, max_length=128)
    auth: constr(min_length=1, max_length=128)


class SubscriptionSchema(BaseModel):
    endpoint: constr(min_length=1, max_length=2048)
    keys: SubscriptionKeysSchema


class PushSubscribeSchema(BaseModel):
    subscription: SubscriptionSchema


class PushSendSchema(BaseModel):
    user_id: Optional[conint(ge=1)] = None
    title: constr(min_length=1, max_length=120) = "QuestByCycle"
    body: constr(min_length=0, max_length=1000) = ""


class ProfileMessageSchema(BaseModel):
    content: constr(min_length=1, max_length=1000)


class SubmissionCommentSchema(BaseModel):
    comment: constr(min_length=0, max_length=1000) = ""


class SubmissionReplySchema(BaseModel):
    content: constr(min_length=1, max_length=1000)


class TimezoneSchema(BaseModel):
    timezone: constr(min_length=1)


class GenerateQuestSchema(BaseModel):
    description: constr(min_length=1, max_length=500)
    game_id: conint(ge=1)


class GenerateBadgeImageSchema(BaseModel):
    badge_description: constr(min_length=1, max_length=500)


class InboxActivitySchema(BaseModel):
    type: constr(min_length=1, max_length=50)
    actor: constr(min_length=1, max_length=255)
    object: Optional[Dict[str, Any]] = None


class UpdateQuestSchema(BaseModel):
    title: Optional[constr(min_length=0, max_length=200)] = None
    description: Optional[constr(min_length=0, max_length=1000)] = None
    tips: Optional[constr(min_length=0, max_length=1000)] = None
    points: Optional[conint(ge=0)] = None
    completion_limit: Optional[conint(ge=0)] = None
    badge_awarded: Optional[conint(ge=0)] = None
    enabled: Optional[bool] = None
    is_sponsored: Optional[bool] = None
    category: Optional[constr(min_length=0, max_length=100)] = None
    verification_type: Optional[constr(min_length=0, max_length=100)] = None
    frequency: Optional[Literal['daily', 'weekly', 'monthly']] = None
    badge_option: Optional[Literal['none', 'individual', 'category', 'both']] = None
    badge_id: Optional[conint(ge=1)] = None
    from_calendar: Optional[bool] = None
    calendar_event_id: Optional[constr(min_length=0, max_length=100)] = None
    calendar_event_start: Optional[constr(min_length=0, max_length=50)] = None


class QuestListQuerySchema(BaseModel):
    include_disabled: bool = False


class UserProfileUpdateSchema(BaseModel):
    display_name: Optional[constr(min_length=1, max_length=100)] = None
    interests: Optional[constr(min_length=0, max_length=500)] = None
    age_group: Optional[Literal["teen", "adult", "senior"]] = None
    profile_picture: Optional[constr(min_length=0, max_length=200)] = None
