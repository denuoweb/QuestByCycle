"""Quest scoring and badge utilities."""
from __future__ import annotations

from datetime import datetime, timedelta

from flask import current_app, url_for

from ..models import db, Quest, Badge, Game, User, UserQuest, QuestSubmission, ShoutBoardMessage
from app.constants import UTC, FREQUENCY_DELTA

MAX_POINTS_INT = 2 ** 63 - 1


def update_user_score(user_id: int) -> bool:
    try:
        user = db.session.get(User, user_id)
        if not user:
            return False
        total_points = sum(
            quest.points_awarded for quest in user.user_quests if quest.points_awarded is not None
        )
        user.score = min(total_points, MAX_POINTS_INT)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False


def can_complete_quest(user_id: int, quest_id: int):
    now = datetime.now(UTC)
    quest = db.session.get(Quest, quest_id)
    if not quest:
        return False, None
    period_start = now - FREQUENCY_DELTA.get(quest.frequency, timedelta(days=1))
    completions_within_period = QuestSubmission.query.filter(
        QuestSubmission.user_id == user_id,
        QuestSubmission.quest_id == quest_id,
        QuestSubmission.timestamp >= period_start,
    ).count()
    can_verify = completions_within_period < quest.completion_limit
    next_eligible_time = None
    if not can_verify:
        first_completion_in_period = QuestSubmission.query.filter(
            QuestSubmission.user_id == user_id,
            QuestSubmission.quest_id == quest_id,
            QuestSubmission.timestamp >= period_start,
        ).order_by(QuestSubmission.timestamp.asc()).first()
        if first_completion_in_period:
            next_eligible_time = (
                first_completion_in_period.timestamp
                + FREQUENCY_DELTA.get(quest.frequency, timedelta(days=1))
            )
    return can_verify, next_eligible_time


def get_last_relevant_completion_time(user_id: int, quest_id: int):
    now = datetime.now(UTC)
    quest = db.session.get(Quest, quest_id)
    if not quest:
        return None
    period_start = now - FREQUENCY_DELTA.get(quest.frequency, timedelta(0))
    last_relevant_completion = QuestSubmission.query.filter(
        QuestSubmission.user_id == user_id,
        QuestSubmission.quest_id == quest_id,
        QuestSubmission.timestamp >= period_start,
    ).order_by(QuestSubmission.timestamp.desc()).first()
    return last_relevant_completion.timestamp if last_relevant_completion else None


def check_and_award_badges(user_id: int, quest_id: int, game_id: int) -> None:
    user = db.session.get(User, user_id)
    quest = db.session.get(Quest, quest_id)
    user_quest = UserQuest.query.filter_by(user_id=user_id, quest_id=quest_id).first()
    if not user_quest:
        return

    if quest.badge and user_quest.completions >= quest.badge_awarded:
        existing_award = ShoutBoardMessage.query.filter_by(
            user_id=user_id,
            game_id=game_id,
        ).filter(
            ShoutBoardMessage.message.contains(f"data-badge-id='{quest.badge.id}'")
        ).first()
        if not existing_award:
            user.badges.append(quest.badge)
            msg = (
                " earned the badge"
                "<a class='quest-title' href='javascript:void(0);' "
                "onclick='openBadgeModal(this)' "
                f"data-badge-id='{quest.badge.id}' "
                f"data-badge-name='{quest.badge.name}' "
                f"data-badge-description='{quest.badge.description}' "
                f"data-badge-image='{quest.badge.image}' "
                f"data-task-name='{quest.title}' "
                f"data-badge-awarded-count='{quest.badge_awarded}' "
                f"data-task-id='{quest.id}' "
                f"data-user-completions='{user_quest.completions}'>"
                f"{quest.badge.name}</a>for completing quest "
                "<a class='quest-title' href='javascript:void(0);' "
                f"onclick='openQuestDetailModal({quest.id})'>"
                f"{quest.title}</a>"
            )
            sbm = ShoutBoardMessage(message=msg, user_id=user_id, game_id=game_id)
            db.session.add(sbm)
            db.session.commit()

    if quest.category and game_id:
        category_quests = Quest.query.filter_by(category=quest.category, game_id=game_id).all()
        if not category_quests:
            return
        completed_quests = [
            ut.quest
            for ut in user.user_quests
            if (
                ut.quest.category == quest.category
                and ut.quest.game_id == game_id
                and ut.completions >= 1
            )
        ]
        if len(completed_quests) == len(category_quests):
            category_badges = Badge.query.filter_by(category=quest.category).all()
            for badge in category_badges:
                existing_award = ShoutBoardMessage.query.filter_by(
                    user_id=user_id,
                    game_id=game_id,
                ).filter(
                    ShoutBoardMessage.message.contains(f"data-badge-id='{badge.id}'")
                ).first()
                if not existing_award:
                    url = url_for("static", filename=f"images/badge_images/{badge.image}")
                    user.badges.append(badge)
                    msg = (
                        " earned the badge "
                        "<a class='quest-title' href='javascript:void(0);' "
                        "onclick='openBadgeModal(this)' "
                        f"data-badge-id='{badge.id}' "
                        f"data-badge-name='{badge.name}' "
                        f"data-badge-description='{badge.description}' "
                        f"data-badge-image='{url}' "
                        f"data-task-name='{quest.title}' "
                        "data-badge-awarded-count='1' "
                        f"data-task-id='{quest.id}' "
                        f"data-user-completed='{len(completed_quests)}' "
                        f"data-total-tasks='{len(category_quests)}'>"
                        f"{badge.name}</a> for completing all quests in category "
                        f"'{quest.category}'"
                    )
                    sbm = ShoutBoardMessage(message=msg, user_id=user_id, game_id=game_id)
                    db.session.add(sbm)
                    db.session.commit()


def check_and_revoke_badges(user_id: int, game_id: int | None = None) -> None:
    user = db.session.get(User, user_id)
    if not user:
        return
    badges_to_remove = []
    for badge in user.badges:
        if badge.category:
            current_category_quests = Quest.query.filter_by(category=badge.category, game_id=game_id).all()
            completed_quests = {
                ut.quest
                for ut in user.user_quests
                if (
                    ut.quest.category == badge.category
                    and ut.quest.game_id == game_id
                    and ut.completions >= 1
                )
            }
            if set(current_category_quests) != set(completed_quests):
                badges_to_remove.append(badge)
        else:
            all_met = True
            for quest in badge.quests:
                user_quest = UserQuest.query.filter_by(user_id=user_id, quest_id=quest.id).first()
                if not user_quest or user_quest.completions < quest.badge_awarded:
                    all_met = False
                    break
            if not all_met:
                badges_to_remove.append(badge)
    for badge in badges_to_remove:
        user.badges.remove(badge)
        messages = ShoutBoardMessage.query.filter_by(user_id=user_id, game_id=game_id).all()
        for message in messages:
            if f"data-badge-id='{badge.id}'" in message.message:
                db.session.delete(message)
        db.session.commit()


def enhance_badges_with_task_info(badges, game_id: int | None = None, user_id: int | None = None):
    enhanced_badges = []
    for badge in badges:
        if game_id:
            awarding_quests = [quest for quest in badge.quests if quest.game_id == game_id]
        else:
            awarding_quests = badge.quests
        if awarding_quests:
            task_names = ", ".join(quest.title for quest in awarding_quests)
            task_ids = ", ".join(str(quest.id) for quest in awarding_quests)
            badge_awarded_counts = ", ".join(str(quest.badge_awarded) for quest in awarding_quests)
        else:
            task_names = ""
            task_ids = ""
            badge_awarded_counts = "1"
        user_completions_total = 0
        is_complete = False
        if awarding_quests and user_id:
            completions_list = []
            for quest in awarding_quests:
                user_quest = UserQuest.query.filter_by(user_id=user_id, quest_id=quest.id).first()
                completions = user_quest.completions if user_quest else 0
                completions_list.append(completions)
                if completions >= quest.badge_awarded:
                    is_complete = True
            user_completions_total = max(completions_list) if completions_list else 0
        enhanced_badges.append(
            {
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "image": badge.image,
                "category": badge.category,
                "task_names": task_names,
                "task_ids": task_ids,
                "badge_awarded_counts": badge_awarded_counts,
                "user_completions": user_completions_total,
                "is_complete": is_complete,
            }
        )
    return enhanced_badges
