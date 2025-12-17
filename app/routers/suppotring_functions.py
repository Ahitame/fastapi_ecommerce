from sqlalchemy import select
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.products import Product as ProductModel
from app.models.reviews import Review as ReviewModel


async def update_product_rating(db: AsyncSession, product_id: int):
    """
    Рассчитывает и обновляет рейтинг выбранного товара
    """
    result = await db.execute(
        select(func.avg(ReviewModel.grade)).where(
            ReviewModel.product_id == product_id,
            ReviewModel.is_active == True
        )
    )
    avg_rating = result.scalar() or 0.0
    product = await db.get(ProductModel, product_id)
    product.rating = round(avg_rating, 2)
    await db.commit()