import os
from dotenv import load_dotenv


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.environ["DATABASE_URL"] # Вернет KeyError, если переменная окружения не установлена
ALGORITHM = "HS256"