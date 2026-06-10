import pytest

from app.models.user import User
from app.repositories.user import UserRepository
from app.services.review import ReviewData, ReviewService
from app.services.toilet import ToiletService
from app.services.user import UserService


async def _force_make_moderator(session, telegram_id: int) -> User:
    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(telegram_id)
    return await repo.set_moderator(user.id, True)

VALID_DATA = ReviewData(
    score_cleanliness=20,
    score_supplies=15,
    score_smell=18,
    score_equipment=12,
    score_privacy=4,
    score_vibe=4,
    comment="Очень достойное заведение",
)


async def _make_user(session, telegram_id):
    s = UserService(session)
    user, _ = await s.get_or_create(telegram_id=telegram_id)
    return user


async def _make_toilet(session, user, address="ул. Тестовая, 1"):
    s = ToiletService(session)
    return await s.create(address=address, created_by=user)


@pytest.mark.asyncio
async def test_create_review(session):
    """Отзыв создаётся, total_score считается правильно."""
    user = await _make_user(session, 20001)
    toilet = await _make_toilet(session, user)
    service = ReviewService(session)

    review = await service.create_review(user=user, toilet_id=toilet.id, data=VALID_DATA)

    assert review.id is not None
    assert review.total_score == 20 + 15 + 18 + 12 + 4 + 4  # == 73
    assert review.is_deleted is False


@pytest.mark.asyncio
async def test_no_duplicate_review(session):
    """Нельзя оставить два отзыва на один туалет."""
    user = await _make_user(session, 20002)
    toilet = await _make_toilet(session, user, "ул. Дублей, 2")
    service = ReviewService(session)

    await service.create_review(user=user, toilet_id=toilet.id, data=VALID_DATA)

    with pytest.raises(ValueError, match="уже оставляли"):
        await service.create_review(user=user, toilet_id=toilet.id, data=VALID_DATA)


@pytest.mark.asyncio
async def test_score_validation_out_of_range(session):
    """Оценка вне диапазона вызывает ошибку."""
    user = await _make_user(session, 20003)
    toilet = await _make_toilet(session, user, "ул. Ошибок, 3")
    service = ReviewService(session)

    bad_data = ReviewData(
        score_cleanliness=99,  # максимум 25!
        score_supplies=15,
        score_smell=18,
        score_equipment=12,
        score_privacy=4,
        score_vibe=4,
    )

    with pytest.raises(ValueError):
        await service.create_review(user=user, toilet_id=toilet.id, data=bad_data)


@pytest.mark.asyncio
async def test_soft_delete_review(session):
    """Модератор удаляет отзыв — он скрыт но в БД остаётся."""
    user = await _make_user(session, 20004)
    mod = await _make_user(session, 20005)

    mod = await _force_make_moderator(session, 20005)

    toilet = await _make_toilet(session, user, "ул. Удалений, 4")
    service = ReviewService(session)

    review = await service.create_review(user=user, toilet_id=toilet.id, data=VALID_DATA)
    deleted = await service.delete_review(mod, review.id, reason="Спам")

    assert deleted.is_deleted is True
    assert deleted.deleted_reason == "Спам"
    assert deleted.deleted_by_id == mod.id


@pytest.mark.asyncio
async def test_only_moderator_can_delete(session):
    """Обычный юзер не может удалить отзыв."""
    user = await _make_user(session, 20006)
    other = await _make_user(session, 20007)
    toilet = await _make_toilet(session, user, "ул. Прав, 5")
    service = ReviewService(session)

    review = await service.create_review(user=user, toilet_id=toilet.id, data=VALID_DATA)

    with pytest.raises(PermissionError):
        await service.delete_review(other, review.id, reason="Хочу удалить")


@pytest.mark.asyncio
async def test_deleted_reviews_not_in_list(session):
    """Удалённые отзывы не видны в обычном списке."""
    user1 = await _make_user(session, 20008)
    user2 = await _make_user(session, 20009)
    mod = await _make_user(session, 20010)

    mod = await _force_make_moderator(session, 20010)

    toilet = await _make_toilet(session, user1, "ул. Видимости, 6")
    service = ReviewService(session)

    r1 = await service.create_review(user=user1, toilet_id=toilet.id, data=VALID_DATA)
    await service.create_review(user=user2, toilet_id=toilet.id, data=VALID_DATA)

    await service.delete_review(mod, r1.id, reason="Тест")

    reviews = await service.get_toilet_reviews(toilet.id)
    assert len(reviews) == 1
    assert reviews[0].user_id == user2.id


@pytest.mark.asyncio
async def test_create_review_with_photos(session):
    """Отзыв сохраняется с фото (file_id строки)."""
    user = await _make_user(session, 30001)
    toilet = await _make_toilet(session, user, "ул. Фотографов, 1")
    service = ReviewService(session)

    data_with_photos = ReviewData(
        score_cleanliness=20,
        score_supplies=15,
        score_smell=18,
        score_equipment=12,
        score_privacy=4,
        score_vibe=4,
        photos=["file_id_aaa", "file_id_bbb"],
    )

    review = await service.create_review(user=user, toilet_id=toilet.id, data=data_with_photos)
    assert review.id is not None

    # Загружаем с фото
    from sqlalchemy import select
    from app.models.review_photo import ReviewPhoto
    result = await session.execute(
        select(ReviewPhoto).where(ReviewPhoto.review_id == review.id).order_by(ReviewPhoto.position)
    )
    photos = result.scalars().all()

    assert len(photos) == 2
    assert photos[0].file_id == "file_id_aaa"
    assert photos[0].position == 1
    assert photos[1].file_id == "file_id_bbb"
    assert photos[1].position == 2


@pytest.mark.asyncio
async def test_photos_capped_at_three(session):
    """Сохраняется максимум 3 фото, лишние обрезаются."""
    user = await _make_user(session, 30002)
    toilet = await _make_toilet(session, user, "ул. Переполненная, 2")
    service = ReviewService(session)

    data_too_many = ReviewData(
        score_cleanliness=20,
        score_supplies=15,
        score_smell=18,
        score_equipment=12,
        score_privacy=4,
        score_vibe=4,
        photos=["fid_1", "fid_2", "fid_3", "fid_4", "fid_5"],
    )

    review = await service.create_review(user=user, toilet_id=toilet.id, data=data_too_many)

    from sqlalchemy import select
    from app.models.review_photo import ReviewPhoto
    result = await session.execute(
        select(ReviewPhoto).where(ReviewPhoto.review_id == review.id)
    )
    photos = result.scalars().all()
    assert len(photos) == 3


@pytest.mark.asyncio
async def test_review_without_photos(session):
    """Отзыв без фото создаётся нормально."""
    user = await _make_user(session, 30003)
    toilet = await _make_toilet(session, user, "ул. Безфото, 3")
    service = ReviewService(session)

    review = await service.create_review(user=user, toilet_id=toilet.id, data=VALID_DATA)

    from sqlalchemy import select
    from app.models.review_photo import ReviewPhoto
    result = await session.execute(
        select(ReviewPhoto).where(ReviewPhoto.review_id == review.id)
    )
    photos = result.scalars().all()
    assert len(photos) == 0
