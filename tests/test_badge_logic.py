import pytest
from datetime import datetime, timedelta, timezone

from app import create_app, db
from app.models import Quest, Badge, Game, User, UserQuest
from app.utils.quest_scoring import check_and_award_badges


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "MAIL_SERVER": None,
        }
    )
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture
def user(app):
    usr = User(
        username="u",
        email="u@example.com",
        license_agreed=True,
        email_verified=True,
    )
    usr.set_password("pw")
    usr.created_at = datetime.now(timezone.utc)
    db.session.add(usr)
    db.session.commit()
    return usr


@pytest.fixture
def game(user):
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = datetime.now(timezone.utc) + timedelta(days=1)
    gm = Game(title="G", start_date=start, end_date=end, admin_id=user.id)
    gm.admins.append(user)
    db.session.add(gm)
    db.session.commit()
    return gm


def _complete_quest(user_id, quest_id, completions=1):
    uq = UserQuest(user_id=user_id, quest_id=quest_id, completions=completions)
    db.session.add(uq)
    db.session.commit()


def test_badge_option_none(user, game):
    badge = Badge(name="Cat", description="c", category="C")
    quest = Quest(
        title="Q",
        game_id=game.id,
        badge_awarded=1,
        category="C",
        badge_option="none",
    )
    db.session.add_all([badge, quest])
    db.session.commit()
    _complete_quest(user.id, quest.id)

    check_and_award_badges(user.id, quest.id, game.id)
    db.session.refresh(user)
    assert len(user.badges) == 0


def test_badge_option_individual(user, game):
    ind_badge = Badge(name="Ind", description="i")
    cat_badge = Badge(name="Cat", description="c", category="C")
    quest = Quest(
        title="Q",
        game_id=game.id,
        badge_awarded=1,
        category="C",
        badge_id=ind_badge.id,
        badge_option="individual",
    )
    db.session.add_all([ind_badge, cat_badge, quest])
    db.session.commit()
    _complete_quest(user.id, quest.id)

    check_and_award_badges(user.id, quest.id, game.id)
    db.session.refresh(user)
    assert {b.name for b in user.badges} == {"Ind"}


def test_badge_option_category(user, game):
    cat_badge = Badge(name="Cat", description="c", category="C")
    quest = Quest(
        title="Q",
        game_id=game.id,
        badge_awarded=1,
        category="C",
        badge_option="category",
    )
    db.session.add_all([cat_badge, quest])
    db.session.commit()
    _complete_quest(user.id, quest.id)

    check_and_award_badges(user.id, quest.id, game.id)
    db.session.refresh(user)
    assert {b.name for b in user.badges} == {"Cat"}


def test_badge_option_both(user, game):
    ind_badge = Badge(name="Ind", description="i")
    cat_badge = Badge(name="Cat", description="c", category="C2")
    quest = Quest(
        title="Q",
        game_id=game.id,
        badge_awarded=1,
        category="C2",
        badge_id=ind_badge.id,
        badge_option="both",
    )
    db.session.add_all([ind_badge, cat_badge, quest])
    db.session.commit()
    _complete_quest(user.id, quest.id)

    check_and_award_badges(user.id, quest.id, game.id)
    db.session.refresh(user)
    assert {b.name for b in user.badges} == {"Ind", "Cat"}
