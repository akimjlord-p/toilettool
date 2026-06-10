import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession, ModeratorUser
from app.schemas.review import (
    DeleteReviewRequest,
    ModeratorReviewResponse,
    ReviewCreate,
    ReviewResponse,
)
from app.services.review import ReviewData, ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _to_review_data(body: ReviewCreate) -> ReviewData:
    return ReviewData(
        score_cleanliness=body.score_cleanliness,
        score_supplies=body.score_supplies,
        score_smell=body.score_smell,
        score_equipment=body.score_equipment,
        score_privacy=body.score_privacy,
        score_vibe=body.score_vibe,
        comment=body.comment,
        photos=body.photos,
    )


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    body: ReviewCreate,
    user: CurrentUser,
    session: DbSession,
):
    """Оставить отзыв на туалет. Один пользователь — один отзыв."""
    service = ReviewService(session)
    try:
        review = await service.create_review(
            user=user,
            toilet_id=body.toilet_id,
            data=_to_review_data(body),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return review


@router.post("/moderator", response_model=ModeratorReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_moderator_review(
    body: ReviewCreate,
    moderator: ModeratorUser,
    session: DbSession,
):
    """Официальный отзыв модератора."""
    service = ReviewService(session)
    try:
        review = await service.create_moderator_review(
            moderator=moderator,
            toilet_id=body.toilet_id,
            data=_to_review_data(body),
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return review


@router.delete("/{review_id}", response_model=ReviewResponse)
async def delete_review(
    review_id: uuid.UUID,
    body: DeleteReviewRequest,
    moderator: ModeratorUser,
    session: DbSession,
):
    """Модератор удаляет отзыв с указанием причины."""
    service = ReviewService(session)
    try:
        review = await service.delete_review(
            moderator=moderator,
            review_id=review_id,
            reason=body.reason,
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return review


@router.get("/toilet/{toilet_id}", response_model=list[ReviewResponse])
async def get_toilet_reviews(toilet_id: uuid.UUID, session: DbSession):
    """Список всех активных отзывов на туалет."""
    service = ReviewService(session)
    return await service.get_toilet_reviews(toilet_id)


@router.get("/toilet/{toilet_id}/moderator", response_model=list[ModeratorReviewResponse])
async def get_moderator_reviews(toilet_id: uuid.UUID, session: DbSession):
    """Список модераторских отзывов на туалет."""
    service = ReviewService(session)
    return await service.get_toilet_moderator_reviews(toilet_id)
