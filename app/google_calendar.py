from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse, parse_qs

from flask import current_app
from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.models import db, Quest, Game

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_calendar_id(calendar_url: str) -> str | None:
    """Extract calendar ID from an embed URL."""
    parsed = urlparse(calendar_url)
    params = parse_qs(parsed.query)
    src = params.get("src")
    if src:
        return src[0]
    return None


def get_calendar_service():
    """Return an authorized Google Calendar service or ``None``."""
    credentials_file = current_app.config.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    if not credentials_file:
        current_app.logger.warning("GOOGLE_SERVICE_ACCOUNT_FILE not configured")
        return None
    creds = service_account.Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    return build("calendar", "v3", credentials=creds)


def sync_game_calendar(game_id: int) -> None:
    """Sync events from a game's calendar into quests."""
    game = db.session.get(Game, game_id)
    if not game or not game.calendar_url:
        return
    service = get_calendar_service()
    if service is None:
        return
    cal_id = _get_calendar_id(game.calendar_url)
    if not cal_id:
        return
    now = datetime.utcnow().isoformat() + "Z"
    events_result = service.events().list(calendarId=cal_id, timeMin=now, singleEvents=True, orderBy="startTime").execute()
    for event in events_result.get("items", []):
        if event.get("status") == "cancelled":
            continue
        event_id = event["id"]
        existing = Quest.query.filter_by(calendar_event_id=event_id).first()
        if existing:
            continue
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
        start_dt = None
        if start:
            start_dt = datetime.fromisoformat(start)
        quest = Quest(
            title=event.get("summary", "Untitled Event"),
            description=event.get("description", ""),
            game_id=game.id,
            calendar_event_id=event_id,
            event_start=start_dt,
        )
        db.session.add(quest)
        db.session.commit()
        link = f"https://questbycycle.org/?quest_shortcut={quest.id}"
        desc = event.get("description", "")
        new_desc = f"View Quest: {link}\n\n{desc}"
        try:
            service.events().patch(calendarId=cal_id, eventId=event_id, body={"description": new_desc}).execute()
        except Exception as exc:  # pragma: no cover - network
            current_app.logger.error("Failed to update event description: %s", exc)

