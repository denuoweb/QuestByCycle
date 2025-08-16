from __future__ import annotations

import os
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

from flask import current_app
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.exc import SQLAlchemyError

from app.utils import format_db_error

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


def _parse_calendar_tz(url: str) -> str | None:
    """Return timezone name from a Google calendar embed URL if present."""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    return qs.get("ctz", [None])[0]


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
        if not os.path.isabs(path):
            path = os.path.join(current_app.static_folder, path)
        if not os.path.isfile(path):
            current_app.logger.warning(
                "Calendar service JSON missing for game %s", game.id
            )
            continue
        creds = Credentials.from_service_account_file(
            path, scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        start_time = now.isoformat()
        end_time = (now + timedelta(days=14)).isoformat()
        events: list[dict] = []
        page_token: str | None = None
        try:
            while True:
                resp = (
                    service.events()
                    .list(
                        calendarId=calendar_id,
                        timeMin=start_time,
                        timeMax=end_time,
                        singleEvents=True,
                        orderBy="startTime",
                        pageToken=page_token,
                    )
                    .execute()
                )
                events.extend(resp.get("items", []))
                page_token = resp.get("nextPageToken")
                if not page_token:
                    break
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
            start_dt = datetime.fromisoformat(start_str) if start_str else None
            if start_dt and not start_dt.tzinfo:
                start_dt = start_dt.replace(tzinfo=UTC)
            description = ev.get("description", "") or ""
            clean_desc = re.sub(
                r'<a href="https://questbycycle.org/\?quest_shortcut=\d+">View Quest</a>\n?',
                "",
                description,
            )
            quest = Quest(
                title=ev.get("summary") or "Calendar Quest",
                description=clean_desc,
                points=100,
                game_id=game.id,
                completion_limit=1,
                frequency="daily",
                category="Calendar",
                verification_type="photo",
                from_calendar=True,
                calendar_event_id=ev_id,
                calendar_event_start=start_dt,
            )
            db.session.add(quest)
            db.session.flush()
            quest_url = f"https://questbycycle.org/?quest_shortcut={quest.id}"
            new_desc = f"<a href=\"{quest_url}\">View Quest</a>\n{clean_desc}"
            try:
                service.events().patch(
                    calendarId=calendar_id,
                    eventId=ev_id,
                    body={"description": new_desc},
                ).execute()
            except HttpError as exc:  # permission or API error
                if getattr(exc.resp, "status", None) == 403:
                    current_app.logger.warning(
                        "Calendar service account lacks permission to update event %s for game %s",
                        ev_id,
                        game.id,
                    )
                else:
                    current_app.logger.warning(
                        "Failed to update event description for game %s: %s",
                        game.id,
                        exc,
                    )
            except Exception as exc:
                current_app.logger.warning(
                    "Could not update event description for game %s: %s",
                    game.id,
                    exc,
                )
        game.last_calendar_sync = now
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        current_app.logger.error(
            "Calendar sync commit failed: %s", format_db_error(exc)
        )
        db.session.rollback()
