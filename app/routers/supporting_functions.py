from sqlalchemy import select
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi import UploadFile, HTTPException, status

from app.models.products import Product as ProductModel
from app.models.reviews import Review as ReviewModel
from app.models.cart_items import CartItem as CartItemModel
from app.models.orders import Order as OrderModel, OrderItem as OrderItemModel

import uuid
from pathlib import Path

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


async def _ensure_product_available(db: AsyncSession, product_id: int) -> None:
    """
    Проверяет существование и активность товара в базе данных.
    Выполняет поиск товара по указанному ID с фильтром по активности.
    """
    result = await db.scalars(
        select(ProductModel).where(
            ProductModel.id == product_id,
            ProductModel.is_active == True,
        )
    )
    product = result.first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive",
        )


async def _get_cart_item(
    db: AsyncSession, user_id: int, product_id: int
) -> CartItemModel | None:
    """
    Получает элемент корзины пользователя для конкретного товара.
    Выполняет поиск записи в корзине по идентификаторам пользователя и товара,
    с предварительной загрузкой связанных данных о товаре.
    """
    result = await db.scalars(
        select(CartItemModel)
        .options(selectinload(CartItemModel.product))
        .where(
            CartItemModel.user_id == user_id,
            CartItemModel.product_id == product_id,
        )
    )
    return result.first()


async def _load_order_with_items(db: AsyncSession, order_id: int) -> OrderModel | None:
    """
    Загрузка заказа с товарами
    """
    result = await db.scalars(
        select(OrderModel)
        .options(
            selectinload(OrderModel.items).selectinload(OrderItemModel.product),
        )
        .where(OrderModel.id == order_id)
    )
    return result.first()



# Изображения
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_ROOT = BASE_DIR / "media" / "products"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2 097 152 байт

async def save_product_image(file: UploadFile) -> str:
    """
    Сохраняет изображение товара и возвращает относительный URL.
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only JPG, PNG or WebP images are allowed")

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Image is too large")

    extension = Path(file.filename or "").suffix.lower() or ".jpg"
    file_name = f"{uuid.uuid4()}{extension}"
    file_path = MEDIA_ROOT / file_name
    file_path.write_bytes(content)

    return f"/media/products/{file_name}"


def remove_product_image(url: str | None) -> None:
    """
    Удаляет файл изображения, если он существует.
    """
    if not url:
        return
    relative_path = url.lstrip("/")
    file_path = BASE_DIR / relative_path
    if file_path.exists():
        file_path.unlink()