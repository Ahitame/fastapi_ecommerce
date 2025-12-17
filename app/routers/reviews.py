from itertools import product

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.products import Product as ProductModel
from app.schemas import Review as ReviewSchema, ReviewCreate
from app.models.categories import Category as CategoryModel
from app.models.users import User as UserModel
from app.auth import get_current_seller, get_current_buyer, get_current_admin
from app.schemas import Product as ProductSchema, ProductCreate
from app.db_depends import get_db

from app.models.reviews import Review as ReviewModel

from sqlalchemy.ext.asyncio import AsyncSession
from app.db_depends import get_async_db


router = APIRouter(
    prefix='/reviews',
    tags=['reviews']
)



@router.get('/', response_model=list[ReviewSchema], status_code=status.HTTP_200_OK)
async def get_reviews(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных отзывов.
    """

    result = await db.scalars(select(ReviewModel).where(ReviewModel.is_active == True))
    return result.all()


@router.get('/products/{product_id}', response_model=list[ReviewSchema], status_code=status.HTTP_200_OK)
async def get_review(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список активных отзывов у указанного товара по его ID.
    """

    # Проверка существования товара
    product_result = await db.scalars(select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True))
    if not product_result.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found or inactive')

    reviews_result = await db.scalars(select(ReviewModel).where(ReviewModel.product_id == product_id, ReviewModel.is_active == True))

    return reviews_result.all()


@router.post('/', response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(review: ReviewCreate, db: AsyncSession = Depends(get_async_db), user: UserModel = Depends(get_current_buyer)):
    """
    Создает отзыв к товару.
    """
    # Проверка существования товара
    product_result = await db.scalars(select(ProductModel).where(ProductModel.id == review.product_id, ProductModel.is_active == True))
    if not product_result.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found or inactive')

    # Проверка отсутствия отзыва
    review_result = await db.scalars(select(ReviewModel).where(ReviewModel.user_id == user.id, ReviewModel.product_id == review.product_id))
    if review_result.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Review already exist')

    if not 1 <= review.grade <= 5:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='Grade must be between 1 and 5')

    # Добавление отзыва в базу данных
    new_review = ReviewModel(**review.model_dump(), user_id=user.id)
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)

    # Обновление рейтинга
    avg_rating_old = await db.scalars(select(ReviewModel.grade).where(ReviewModel.product_id == new_review.product_id, ReviewModel.is_active == True))
    avg_rating_new = round((sum(avg_rating_old.all())) / len(avg_rating_old.all()), 2)

    await db.execute(update(ProductModel).where(ProductModel.id == new_review.product_id).values(rating=avg_rating_new))
    await db.commit()

    return new_review


@router.delete('/{review_id}')
async def delete_review(review_id: int, db: AsyncSession = Depends(get_async_db), user: UserModel = Depends(get_current_admin)):
    """
    Мягкое удаление отзыва
    """
    # Проверка существования отзыва
    review_result = await db.scalar(select(ReviewModel).where(ReviewModel.id == review_id, ReviewModel.is_active == True))
    if not review_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Review not found or inactive')

    # Удаление отзыва
    await db.execute(update(ReviewModel).where(ReviewModel.id == review_id).values(is_active=False))

    await db.commit()
    await db.refresh(review_result)

    # Обновление рейтинга
    grades = await db.scalars(select(ReviewModel.grade).where(ReviewModel.product_id == review_result.product_id, ReviewModel.is_active == True))
    rating_new = round(sum(grades.all()) / len(grades.all()), 2)

    await db.execute(update(ProductModel).where(ProductModel.id == review_result.product_id).values(rating=rating_new))
    await db.commit()

    return {"message": "Review deleted"}












