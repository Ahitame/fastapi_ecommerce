# FastAPI Ecommerce

REST API интернет-магазина на FastAPI и PostgreSQL.
Реализованы API для пользователей, категорий, товаров, корзины, заказов и отзывов.

## Локальный запуск

Требования: Python 3.13 и PostgreSQL.

```powershell
git clone https://github.com/Ahitame/fastapi_ecommerce.git
cd fastapi_ecommerce
python -m pip install -r requirements.txt
```

Создайте пустую базу `ecommerce_db` в PostgreSQL. Укажите параметры подключения и секретный ключ в созданный `.env`:

```
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/ecommerce_db
SECRET_KEY=YOUR_RANDOM_SECRET_KEY
```

Создайте таблицы и запустите приложение:

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Посмотреть документацию и выполнить проверку API: http://127.0.0.1:8000/docs

## Запуск через Docker

Требуется установленный Docker Desktop.

```powershell
git clone https://github.com/Ahitame/fastapi_ecommerce.git
cd fastapi_ecommerce
```

Создайте файл `.env`.

```powershell
docker compose up --build -d
```



