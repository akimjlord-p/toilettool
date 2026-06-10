import uuid
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.moderator_review import ModeratorReview
from app.models.review import Review
from app.models.review_photo import ReviewPhoto
from app.models.user import User
from app.repositories.moderator_review import ModeratorReviewRepository
from app.repositories.review import ReviewRepository

# Максимальные значения по каждому критерию
SCORE_LIMITS = {
    "score_cleanliness": 25,
    "score_supplies": 20,
    "score_smell": 20,
    "score_equipment": 15,
    "score_privacy": 5,
    "score_vibe": 5,
}


@dataclass
class ReviewData:
    score_cleanliness: int
    score_supplies: int
    score_smell: int
    score_equipment: int
    score_privacy: int
    score_vibe: int
    comment: str | None = None
    photos: list[str] = field(default_factory=list)  # до 3 Telegram file_id


def _validate_scores(data: ReviewData) -> None:
    """Проверяет что все оценки в допустимых пределах."""
    errors = []
    for field, max_val in SCORE_LIMITS.items():
        value = getattr(data, field)
        if not (0 <= value <= max_val):
            errors.append(f"{field}: должно быть от 0 до {max_val}, получено {value}")
    if errors:
        raise ValueError("\n".join(errors))


def _calc_total(data: ReviewData) -> int:
    return (
        data.score_cleanliness
        + data.score_supplies
        + data.score_smell
        + data.score_equipment
        + data.score_privacy
        + data.score_vibe
    )


class ReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ReviewRepository(session)
        self.mod_repo = ModeratorReviewRepository(session)

    async def create_review(
        self,
        user: User,
        toilet_id: uuid.UUID,
        data: ReviewData,
    ) -> Review:
        """
        Создать отзыв пользователя.
        - Проверяет что юзер ещё не оценивал этот туалет
        - Валидирует оценки
        - Считает total_score
        """
        existing = await self.repo.get_by_user_and_toilet(user.id, toilet_id)
        if existing:
            raise ValueError("Вы уже оставляли отзыв на этот туалет")

        _validate_scores(data)

        review = Review(
            toilet_id=toilet_id,
            user_id=user.id,
            score_cleanliness=data.score_cleanliness,
            score_supplies=data.score_supplies,
            score_smell=data.score_smell,
            score_equipment=data.score_equipment,
            score_privacy=data.score_privacy,
            score_vibe=data.score_vibe,
            total_score=_calc_total(data),
            comment=data.comment,
        )
        created = await self.repo.create(review)

        for i, file_id in enumerate(data.photos[:3], start=1):
            photo = ReviewPhoto(review_id=created.id, file_id=file_id, position=i)
            self.repo.session.add(photo)
        if data.photos:
            await self.repo.session.commit()
            review_id = created.id  # сохраняем до expire
            self.repo.session.expire(created)
            created = await self.repo.get_by_id(review_id)

        return created

    async def create_moderator_review(
        self,
        moderator: User,
        toilet_id: uuid.UUID,
        data: ReviewData,
        is_official: bool = True,
    ) -> ModeratorReview:
        """
        Создать официальный отзыв модератора.
        Один модератор — один отзыв на туалет.
        """
        if not moderator.is_moderator:
            raise PermissionError("Только модераторы могут оставлять официальные отзывы")

        existing = await self.mod_repo.get_by_moderator_and_toilet(moderator.id, toilet_id)
        if existing:
            raise ValueError("Вы уже оставляли модераторский отзыв на этот туалет")

        _validate_scores(data)

        review = ModeratorReview(
            toilet_id=toilet_id,
            moderator_id=moderator.id,
            score_cleanliness=data.score_cleanliness,
            score_supplies=data.score_supplies,
            score_smell=data.score_smell,
            score_equipment=data.score_equipment,
            score_privacy=data.score_privacy,
            score_vibe=data.score_vibe,
            total_score=_calc_total(data),
            comment=data.comment,
            is_official=is_official,
        )
        return await self.mod_repo.create(review)

    async def delete_review(
        self,
        moderator: User,
        review_id: uuid.UUID,
        reason: str,
    ) -> Review:
        """Модератор удаляет отзыв с указанием причины (soft delete)."""
        if not moderator.is_moderator:
            raise PermissionError("Только модераторы могут удалять отзывы")

        review = await self.repo.soft_delete(review_id, moderator.id, reason)
        if not review:
            raise ValueError("Отзыв не найден или уже удалён")

        return review

    async def get_toilet_reviews(
        self,
        toilet_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> list[Review]:
        return await self.repo.get_by_toilet(toilet_id, include_deleted=include_deleted)

    async def get_toilet_moderator_reviews(self, toilet_id: uuid.UUID) -> list[ModeratorReview]:
        return await self.mod_repo.get_by_toilet(toilet_id)

    async def user_already_reviewed(self, user_id: uuid.UUID, toilet_id: uuid.UUID) -> bool:
        """Проверка — юзер уже оценивал этот туалет?"""
        review = await self.repo.get_by_user_and_toilet(user_id, toilet_id)
        return review is not None
