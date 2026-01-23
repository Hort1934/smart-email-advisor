# Smart Email Advisor - Docker Setup

Повна конфігурація для розгортання системи з використанням Docker та Docker Compose.

## 📋 Вимоги

- Docker Engine 20.10+
- Docker Compose 2.0+
- OpenAI API ключ

## 🚀 Швидкий старт

### 1. Клонування проекту
```bash
git clone <repository-url>
cd smart-email-advisor
```

### 2. Налаштування змінних середовища
```bash
# Скопіювати шаблон
cp .env.docker .env

# Відредагувати .env файл
nano .env
```

**Обов'язково налаштуйте:**
```env
OPENAI_API_KEY=your-actual-openai-api-key-here
SECRET_KEY=your-secure-secret-key
```

### 3. Запуск для розробки

**Через Makefile (рекомендовано):**
```bash
make dev
```

**Або через скрипт:**
```bash
# Linux/Mac
./scripts/dev-start.sh

# Windows
scripts\dev-start.bat
```

**Або безпосередньо через Docker Compose:**
```bash
docker-compose up --build -d
```

## 🌐 Доступні сервіси

| Сервіс | URL | Опис |
|--------|-----|------|
| **API документація** | http://localhost:8000/docs | Swagger UI |
| **Backend API** | http://localhost:8000 | FastAPI додаток |
| **Health Check** | http://localhost:8000/health | Статус системи |
| **Adminer** | http://localhost:8080 | Управління БД |
| **PostgreSQL** | localhost:5432 | База даних |
| **Redis** | localhost:6379 | Кеш |

### Доступ до Adminer
- **Сервер:** `db`
- **Користувач:** `postgres`
- **Пароль:** `postgres123`
- **База даних:** `smart_email_advisor`

## 🔧 Команди управління

### Через Makefile
```bash
make help          # Показати всі команди
make dev           # Запуск для розробки
make prod          # Запуск для продакшену
make stop          # Зупинити всі сервіси
make clean         # Повне очищення
make logs          # Показати логи
make shell         # Зайти в shell бекенду
make test          # Запустити тести
make backup-db     # Backup бази даних
```

### Через Docker Compose
```bash
# Основні команди
docker-compose up -d                    # Запустити в фоні
docker-compose up --build -d            # Пересібрати та запустити
docker-compose down                     # Зупинити
docker-compose logs -f backend          # Логи бекенду
docker-compose ps                       # Статус контейнерів

# Профілі
docker-compose --profile dev up -d      # З Adminer
docker-compose --profile production up -d # З Nginx
docker-compose --profile frontend up -d   # З фронтендом (коли буде)
```

## 📁 Структура проекту

```
smart-email-advisor/
├── docker-compose.yml          # Основна конфігурація
├── .env.docker                 # Шаблон змінних середовища
├── Makefile                    # Команди управління
├── backend/
│   ├── Dockerfile              # Docker образ бекенду
│   ├── init.sql                # Ініціалізація БД
│   └── ...
├── nginx/
│   └── nginx.conf              # Конфігурація Nginx
├── scripts/
│   ├── dev-start.sh            # Скрипт розробки (Linux/Mac)
│   ├── dev-start.bat           # Скрипт розробки (Windows)
│   └── prod-deploy.sh          # Скрипт продакшену
└── frontend/                   # (майбутній фронтенд)
```

## 🐳 Сервіси в Docker Compose

### Backend
- **Образ:** Побудований з `./backend/Dockerfile`
- **Порти:** 8000:8000
- **Залежності:** PostgreSQL, Redis
- **Health Check:** `/health` endpoint

### PostgreSQL
- **Образ:** `postgres:15`
- **Порти:** 5432:5432
- **Дані:** Persistent volume `postgres_data`
- **Ініціалізація:** `backend/init.sql`

### Redis
- **Образ:** `redis:7-alpine`
- **Порти:** 6379:6379
- **Дані:** Persistent volume `redis_data`

### Nginx (Production)
- **Образ:** `nginx:alpine`
- **Порти:** 80:80, 443:443
- **Конфігурація:** `nginx/nginx.conf`
- **Профіль:** `production`

### Adminer (Development)
- **Образ:** `adminer`
- **Порти:** 8080:8080
- **Профіль:** `dev`

## 🔒 Безпека

### Для розробки
- Використовуються стандартні паролі
- DEBUG режим увімкнений
- CORS дозволяє всі домени

### Для продакшену
```bash
# Змініть в .env файлі:
SECRET_KEY=your-very-secure-secret-key
DEBUG=false
POSTGRES_PASSWORD=secure-password
```

## 🧪 Тестування API

### Демо endpoints (без авторизації)
```bash
# Health check
curl http://localhost:8000/health

# Демо аналіз листа
curl -X POST "http://localhost:8000/api/demo/analyze-demo" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Важлива зустріч",
    "content": "Привіт! Нагадую про зустріч завтра о 14:00.",
    "sender": "test@example.com",
    "recipient": "user@example.com"
  }'
```

### З авторизацією
```bash
# Логін
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass"}' \
  | jq -r '.access_token')

# Аналіз з токеном
curl -X POST "http://localhost:8000/api/emails/analyze" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Важлива зустріч",
    "content": "Привіт! Нагадую про зустріч завтра о 14:00.",
    "sender": "test@example.com",
    "recipient": "user@example.com"
  }'
```

## 🛠️ Розробка

### Локальні зміни
Папка `./backend` монтується як volume, тому зміни в коді одразу відображаються.

### Логи та дебагінг
```bash
# Всі логи
docker-compose logs -f

# Тільки бекенд
docker-compose logs -f backend

# Зайти в контейнер
docker-compose exec backend bash
```

### Робота з базою даних
```bash
# PostgreSQL shell
docker-compose exec db psql -U postgres -d smart_email_advisor

# Або через Adminer: http://localhost:8080
```

## 🚨 Вирішення проблем

### Порти зайняті
```bash
# Перевірити які порти зайняті
netstat -tulpn | grep :8000

# Змінити порти в docker-compose.yml
```

### Проблеми з дозволами
```bash
# Linux/Mac - дати права на виконання скриптів
chmod +x scripts/*.sh

# Змінити власника файлів
sudo chown -R $USER:$USER .
```

### Очищення системи
```bash
# Повне очищення Docker
make clean

# Або вручну
docker-compose down -v
docker system prune -a -f
```

### База даних не запускається
```bash
# Перевірити логи
docker-compose logs db

# Видалити volume та пересоздати
docker-compose down -v
docker-compose up -d db
```

## 📞 Підтримка

Якщо виникли проблеми:

1. Перевірте логи: `make logs`
2. Перезапустіть: `make restart`
3. Повне очищення: `make clean && make dev`
4. Перевірте наявність OPENAI_API_KEY в .env файлі