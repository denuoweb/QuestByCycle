import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest

from app import create_app, db
from app.models.game import Game
from app.models.quest import Quest
from app.utils import calendar_utils


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "MAIL_SERVER": None,
    })
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()
    ctx.pop()


def test_calendar_sync_creates_photo_quest(app, monkeypatch, tmp_path):
    with app.app_context():
        service_file = tmp_path / "svc.json"
        service_file.write_text("{}")
        game = Game(
            title="CalGame",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=1),
            admin_id=1,
            calendar_service_json_path=str(service_file),
            calendar_url="https://calendar.google.com/calendar/embed?src=test",
        )
        db.session.add(game)
        db.session.commit()

        start = datetime.now(timezone.utc)

        class FakeEvents:
            def list(self, **_):
                return self
            def patch(self, **_):
                class X:
                    def execute(self):
                        pass
                return X()
            def execute(self):
                return {
                    "items": [
                        {
                            "id": "E1",
                            "summary": "Event",
                            "description": "desc",
                            "start": {"dateTime": start.isoformat()},
                        }
                    ]
                }

        class FakeService:
            def events(self):
                return FakeEvents()

        monkeypatch.setattr(calendar_utils.Credentials, "from_service_account_file", lambda *a, **k: None)
        monkeypatch.setattr(calendar_utils, "build", lambda *a, **k: FakeService())

        calendar_utils.sync_google_calendar_events()

        quest = Quest.query.filter_by(calendar_event_id="E1").first()
        assert quest is not None
        assert quest.points == 100
        assert quest.verification_type == "photo"


def test_calendar_sync_strips_link_from_description(app, monkeypatch, tmp_path):
    with app.app_context():
        service_file = tmp_path / "svc.json"
        service_file.write_text("{}")
        game = Game(
            title="CalGame",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=1),
            admin_id=1,
            calendar_service_json_path=str(service_file),
            calendar_url="https://calendar.google.com/calendar/embed?src=test",
        )
        db.session.add(game)
        db.session.commit()

        start = datetime.now(timezone.utc)
        raw_desc = (
            '<a href="https://questbycycle.org/?quest_shortcut=1">View Quest</a>\n'
            'Meet at the park.'
        )

        class FakeEvents:
            def list(self, **_):
                return self

            def patch(self, **_):
                class X:
                    def execute(self):
                        pass

                return X()

            def execute(self):
                return {
                    "items": [
                        {
                            "id": "E2",
                            "summary": "Event",
                            "description": raw_desc,
                            "start": {"dateTime": start.isoformat()},
                        }
                    ]
                }

        class FakeService:
            def events(self):
                return FakeEvents()

        monkeypatch.setattr(calendar_utils.Credentials, "from_service_account_file", lambda *a, **k: None)
        monkeypatch.setattr(calendar_utils, "build", lambda *a, **k: FakeService())

        calendar_utils.sync_google_calendar_events()

        quest = Quest.query.filter_by(calendar_event_id="E2").first()
        assert quest is not None
        assert quest.description == "Meet at the park."


def test_calendar_sync_relative_service_path(app, monkeypatch, tmp_path):
    with app.app_context():
        service_dir = Path(app.static_folder) / "service_json"
        service_dir.mkdir(parents=True, exist_ok=True)
        service_file = service_dir / "svc.json"
        service_file.write_text("{}")
        game = Game(
            title="RelPath",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=1),
            admin_id=1,
            calendar_service_json_path=os.path.join("service_json", service_file.name),
            calendar_url="https://calendar.google.com/calendar/embed?src=test",
        )
        db.session.add(game)
        db.session.commit()

        start = datetime.now(timezone.utc)

        class FakeEvents:
            def list(self, **_):
                return self

            def patch(self, **_):
                class X:
                    def execute(self):
                        pass

                return X()

            def execute(self):
                return {
                    "items": [
                        {
                            "id": "E3",
                            "summary": "Event",
                            "description": "desc",
                            "start": {"dateTime": start.isoformat()},
                        }
                    ]
                }

        class FakeService:
            def events(self):
                return FakeEvents()

        monkeypatch.setattr(calendar_utils.Credentials, "from_service_account_file", lambda *a, **k: None)
        monkeypatch.setattr(calendar_utils, "build", lambda *a, **k: FakeService())

        calendar_utils.sync_google_calendar_events()

        quest = Quest.query.filter_by(calendar_event_id="E3").first()
        assert quest is not None
