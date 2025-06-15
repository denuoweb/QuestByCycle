from __future__ import annotations

from datetime import datetime
import os
from typing import Optional

from flask import current_app
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from app.models import db
from app.models.game import Game
from app.models.quest import Quest

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_service():
    cred_path = current_app.config.get("GOOGLE_CALENDAR_CREDENTIALS")
    if not cred_path or not os.path.exists(cred_path):
        current_app.logger.info("Google Calendar credentials not configured")
        return None
    credentials = Credentials.from_service_account_file(cred_path, scopes=SCOPES)
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


def sync_google_calendars() -> None:
    """Create quests for new calendar events."""
    service = _get_service()
    if not service:
        return
    games = Game.query.filter(Game.google_calendar_id.isnot(None)).all()
    for game in games:
        current_app.logger.info("Syncing calendar for game %s", game.id)
        _sync_game_calendar(service, game)


def _parse_date(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.utcnow()


def _sync_game_calendar(service, game: Game) -> None:
    events = (
        service.events()
        .list(calendarId=game.google_calendar_id, singleEvents=True, orderBy="startTime")
        .execute()
        .get("items", [])
    )
    current_app.logger.info("Fetched %s events for game %s", len(events), game.id)
    for evt in events:
        evt_id = evt.get("id")
        if not evt_id:
            continue
        if Quest.query.filter_by(calendar_event_id=evt_id, game_id=game.id).first():
            continue
        title = evt.get("summary", "Untitled Event")
        description = evt.get("description", "") or ""
        start = evt.get("start", {}).get("dateTime") or evt.get("start", {}).get("date")
        start_dt = _parse_date(start) if start else None

        quest = Quest(
            title=title,
            description=description,
            game_id=game.id,
            calendar_event_id=evt_id,
            is_calendar=True,
            calendar_event_start=start_dt,
        )
        db.session.add(quest)
        db.session.commit()
        current_app.logger.info("Created quest %s from event %s", quest.id, evt_id)

        view_url = f"https://questbycycle.org/?quest_shortcut={quest.id}"
        new_desc = f"View Quest: {view_url}\n\n{description}"
        patch_body = {"description": new_desc}
        try:
            service.events().patch(
                calendarId=game.google_calendar_id,
                eventId=evt_id,
                body=patch_body,
            ).execute()
        except Exception as exc:
            current_app.logger.warning("Failed updating event %s: %s", evt_id, exc)

