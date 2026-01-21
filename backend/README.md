# Smart Email Advisor - Backend

## Опис
Backend частина Smart Email Advisor - AI-орієнтованого сервісу для інтелектуального аналізу вхідних електронних листів та надання користувачу контекстних рекомендацій щодо ефективної роботи з поштою.

## Функціональність

### Основні можливості:
- **AI аналіз електронних листів** - автоматичне визначення пріоритету, категорії та тональності
- **Генерація резюме** - створення коротких резюме для довгих листів
- **Розумні рекомендації** - контекстні поради щодо відповідей та дій
- **Аналітика** - детальна статистика та метрики роботи з поштою
- **Пакетна обробка** - аналіз декількох листів одночасно

### API Endpoints:

#### Автентифікація:
- `POST /api/auth/register` - реєстрація нового користувача
- `POST /api/auth/login` - авторизація користувача
- `GET /api/auth/me` - інформація про поточного користувача
- `POST /api/auth/refresh` - оновлення токену

#### Аналіз електронної пошти:
- `POST /api/emails/analyze` - аналіз окремого листа
- `POST /api/emails/summarize` - створення резюме листа
- `POST /api/emails/recommendations` - отримання рекомендацій
- `POST /api/emails/batch-analyze` - пакетний аналіз листів

#### Аналітика:
- `GET /api/analytics/dashboard` - метрики дашборду
- `GET /api/analytics/activity` - статистика активності
- `GET /api/analytics/trends` - тренди по електронній пошті
- `GET /api/analytics/performance` - аналіз ефективності
- `GET /api/analytics/export` - експорт даних

## Технологічний стек

- **Framework**: FastAPI
- **Database**: PostgreSQL + MongoDB
- **AI**: OpenAI GPT-4 + LangChain
- **Cache**: Redis
- **Auth**: JWT + bcrypt
- **Testing**: pytest + httpx

## Встановлення та запуск

### Локальне середовище:

1. Клонуйте репозиторій та перейдіть до директорії backend:
```bash
cd backend
```

2. Створіть віртуальне середовище:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Встановіть залежності:
```bash
pip install -r requirements.txt
```

4. Налаштуйте змінні середовища:
```bash
cp .env.example .env
# Відредагуйте .env файл з вашими налаштуваннями
```

5. Запустіть сервер:
```bash
uvicorn main:app --reload
```

API буде доступне за адресою: http://localhost:8000
Документація: http://localhost:8000/docs

### Docker запуск:

```bash
# Збірка образу
docker build -t smart-email-advisor-backend .

# Запуск контейнера
docker run -p 8000:8000 --env-file .env smart-email-advisor-backend
```

## Конфігурація

### Обов'язкові змінні середовища:
- `DATABASE_URL` - URL PostgreSQL бази даних
- `MONGODB_URL` - URL MongoDB бази даних
- `REDIS_URL` - URL Redis сервера
- `OPENAI_API_KEY` - ключ OpenAI API
- `SECRET_KEY` - секретний ключ для JWT

### Опціональні налаштування:
- `DEBUG` - режим налагодження (default: False)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - час життя токену (default: 30)
- `ALGORITHM` - алгоритм JWT (default: HS256)

## Структура проекту

```
backend/
├── app/
│   ├── models/
│   │   ├── database.py      # Моделі бази даних
│   │   └── schemas.py       # Pydantic схеми
│   ├── routes/
│   │   ├── auth_routes.py   # Роути автентифікації
│   │   ├── email_routes.py  # Роути аналізу пошти
│   │   └── analytics_routes.py # Роути аналітики
│   └── services/
│       ├── database.py      # Налаштування бази даних
│       └── ai_service.py    # AI сервіс
├── tests/
│   └── test_main.py        # Тести
├── main.py                 # Головний файл додатку
├── requirements.txt        # Python залежності
├── Dockerfile             # Docker конфігурація
└── README.md              # Документація
```

## Тестування

Запуск тестів:
```bash
pytest tests/ -v
```

Запуск з покриттям:
```bash
pytest tests/ --cov=app --cov-report=html
```

## API Документація

Після запуску сервера, повна API документація доступна за адресами:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Розробка

### Додавання нових функцій:
1. Створіть нову гілку: `git checkout -b feature-name`
2. Додайте необхідні моделі в `app/models/`
3. Створіть або оновіть роути в `app/routes/`
4. Додайте бізнес-логіку в `app/services/`
5. Напишіть тести в `tests/`
6. Запустіть тести: `pytest`
7. Створіть pull request

### Корисні команди:
```bash
# Автоформатування коду
black app/ tests/

# Перевірка типів
mypy app/

# Лінтинг
flake8 app/ tests/
```

## Ліцензія

Див. файл LICENSE в корені проекту.