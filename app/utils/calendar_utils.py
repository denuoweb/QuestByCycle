from __future__ import annotations

import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

from flask import current_app
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from sqlalchemy.exc import SQLAlchemyError

from app.constants import UTC
from app.models import db
from app.models.game import Game
from app.models.quest import Quest


def _parse_calendar_id(url: str) -> str | None:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "src" in qs:
        return qs["src"][0]
    if parsed.path:
        return parsed.path.rstrip("/").split("/")[-1]
    return None


def sync_google_calendar_events() -> None:
    """Create quests from new Google Calendar events."""
    games = Game.query.filter(
        Game.calendar_service_json_path.isnot(None),
        Game.calendar_url.isnot(None),
    ).all()
    now = datetime.now(UTC)
    for game in games:
        calendar_id = _parse_calendar_id(game.calendar_url)
        if not calendar_id:
            continue
        path = game.calendar_service_json_path
        if not os.path.isfile(path):
            current_app.logger.warning(
                "Calendar service JSON missing for game %s", game.id
            )
            continue
        creds = Credentials.from_service_account_file(
            path, scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        start_time = (game.last_calendar_sync or now - timedelta(days=7)).isoformat()
        try:
            events = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=start_time,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
                .get("items", [])
            )
        except Exception as exc:  # network or API error
            current_app.logger.error(
                "Failed to fetch calendar events for game %s: %s", game.id, exc
            )
            continue
        for ev in events:
            ev_id = ev.get("id")
            if not ev_id:
                continue
            if Quest.query.filter_by(calendar_event_id=ev_id, game_id=game.id).first():
                continue
            start_str = ev.get("start", {}).get("dateTime")
            start_dt = (
                datetime.fromisoformat(start_str).astimezone(UTC) if start_str else None
            )
            quest = Quest(
                title=ev.get("summary") or "Calendar Quest",
                description=ev.get("description") or "",
                points=1,
                game_id=game.id,
                completion_limit=1,
                frequency="daily",
                category="Calendar",
                verification_type="comment",
                from_calendar=True,
                calendar_event_id=ev_id,
                calendar_event_start=start_dt,
            )
            db.session.add(quest)
            db.session.flush()
            quest_url = f"https://questbycycle.org/?quest_shortcut={quest.id}"
            new_desc = f"View Quest: {quest_url}\n{ev.get('description', '')}"
            try:
                service.events().patch(
                    calendarId=calendar_id,
                    eventId=ev_id,
                    body={"description": new_desc},
                ).execute()
            except Exception:
                current_app.logger.warning(
                    "Could not update event description for game %s", game.id
                )
        game.last_calendar_sync = now
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        current_app.logger.error("Calendar sync commit failed: %s", exc)
        db.session.rollback()
