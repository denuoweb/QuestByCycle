import pytest
from datetime import datetime, timedelta, timezone

from app import create_app, db
from app.models.game import Game
from app.models.user import User
from app.models.quest import Quest, QuestSubmission
from app.models.badge import Badge
from app.main import _prepare_quests, _prepare_user_data, _sort_calendar_quests


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


def test_prepare_quests_hides_unbadged_empty(app):
    with app.app_context():
        admin = User(username="admin", email="admin@example.com", license_agreed=True)
        admin.set_password("pw")
        db.session.add(admin)
        db.session.commit()

        game = Game(
            title="Test Game",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=1),
            admin_id=admin.id,
        )
        db.session.add(game)
        game.admins.append(admin)
        db.session.commit()

        badge = Badge(name="B")
        db.session.add(badge)
        db.session.commit()

        q1 = Quest(title="q1", game=game)
        q2 = Quest(title="q2", game=game, badge_id=badge.id)
        db.session.add_all([q1, q2])
        db.session.commit()

        sub = QuestSubmission(quest_id=q2.id, user_id=admin.id)
        db.session.add(sub)
        db.session.commit()

        quests, _ = _prepare_quests(game, admin.id, [], datetime.now(timezone.utc))
        ids = [q.id for q in quests]
        assert q1.id not in ids
        assert q2.id in ids


def test_prepare_quests_hides_badgeless_image(app):
    with app.app_context():
        admin = User(username="admin2", email="admin2@example.com", license_agreed=True)
        admin.set_password("pw")
        db.session.add(admin)
        db.session.commit()

        game = Game(
            title="Test Game2",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=1),
            admin_id=admin.id,
        )
        db.session.add(game)
        game.admins.append(admin)
        db.session.commit()

        b_no_img = Badge(name="B1")
        b_img = Badge(name="B2", image="img.png")
        db.session.add_all([b_no_img, b_img])
        db.session.commit()

        q1 = Quest(title="q1", game=game, badge_id=b_no_img.id)
        q2 = Quest(title="q2", game=game, badge_id=b_img.id)
        q3 = Quest(title="q3", game=game, badge_id=b_no_img.id)
        db.session.add_all([q1, q2, q3])
        db.session.commit()

        sub = QuestSubmission(quest_id=q3.id, user_id=admin.id)
        db.session.add(sub)
        db.session.commit()

        quests, _ = _prepare_quests(game, admin.id, [], datetime.now(timezone.utc))
        ids = [q.id for q in quests]
        assert q1.id not in ids
        assert q2.id in ids
        assert q3.id in ids


def test_prepare_user_data_hides_badgeless_image(app):
    with app.app_context():
        admin = User(username="admin3", email="admin3@example.com", license_agreed=True)
        admin.set_password("pw")
        db.session.add(admin)
        db.session.commit()

        game = Game(
            title="Test Game3",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=1),
            admin_id=admin.id,
        )
        db.session.add(game)
        game.admins.append(admin)
        db.session.commit()

        b_no_img = Badge(name="B1")
        b_img = Badge(name="B2", image="img.png")
        db.session.add_all([b_no_img, b_img])
        db.session.commit()

        q1 = Quest(title="q1", game=game, badge_id=b_no_img.id)
        q2 = Quest(title="q2", game=game, badge_id=b_img.id)
        db.session.add_all([q1, q2])
        db.session.commit()

        earned, unearned = _prepare_user_data(game.id, admin)
        all_badges = [b['id'] for b in earned + unearned]
        assert b_no_img.id not in all_badges
        assert b_img.id in all_badges


def test_prepare_quests_includes_calendar_quests(app):
    with app.app_context():
        admin = User(username="admin4", email="admin4@example.com", license_agreed=True)
        admin.set_password("pw")
        db.session.add(admin)
        db.session.commit()

        game = Game(
            title="Calendar Game",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=1),
            admin_id=admin.id,
        )
        db.session.add(game)
        game.admins.append(admin)
        db.session.commit()

        q_cal = Quest(title="Calendar", game=game, from_calendar=True)
        db.session.add(q_cal)
        db.session.commit()

        quests, _ = _prepare_quests(game, admin.id, [], datetime.now(timezone.utc))
        ids = [q.id for q in quests]
        assert q_cal.id in ids


def test_sort_calendar_quests_orders_by_date(app):
    with app.app_context():
        admin = User(username="admin5", email="admin5@example.com", license_agreed=True)
        admin.set_password("pw")
        db.session.add(admin)
        db.session.commit()

        game = Game(
            title="Calendar Game",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=1),
            admin_id=admin.id,
        )
        db.session.add(game)
        game.admins.append(admin)
        db.session.commit()

        future1 = Quest(
            title="Future1",
            game=game,
            from_calendar=True,
            calendar_event_start=datetime.now(timezone.utc) + timedelta(days=1),
        )
        future2 = Quest(
            title="Future2",
            game=game,
            from_calendar=True,
            calendar_event_start=datetime.now(timezone.utc) + timedelta(days=2),
        )
        past = Quest(
            title="Past",
            game=game,
            from_calendar=True,
            calendar_event_start=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db.session.add_all([future2, future1, past])
        db.session.commit()

        ordered = _sort_calendar_quests([future2, future1, past], datetime.now(timezone.utc))
        titles = [q.title for q in ordered]
        assert titles == ["Future1", "Future2", "Past"]


def test_calendar_quest_can_verify_after_start(app):
    with app.app_context():
        admin = User(username="admin6", email="admin6@example.com", license_agreed=True)
        admin.set_password("pw")
        db.session.add(admin)
        db.session.commit()

        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        game = Game(
            title="Calendar Game",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=1),
            admin_id=admin.id,
        )
        db.session.add(game)
        game.admins.append(admin)
        db.session.commit()

        quest = Quest(
            title="Future Quest",
            game=game,
            from_calendar=True,
            calendar_event_start=start_time,
        )
        db.session.add(quest)
        db.session.commit()

        quests, _ = _prepare_quests(game, admin.id, [], datetime.now(timezone.utc))
        q = next(q for q in quests if q.id == quest.id)
        assert not q.can_verify
        assert q.next_eligible_time == start_time

        later = start_time + timedelta(minutes=1)
        quests, _ = _prepare_quests(game, admin.id, [], later)
        q = next(q for q in quests if q.id == quest.id)
        assert q.can_verify
