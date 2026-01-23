@echo off
REM Smart Email Advisor - Development Setup Script для Windows

echo 🚀 Запуск Smart Email Advisor для розробки...

REM Перевірка наявності .env файлу
if not exist .env (
    echo 📋 Створення .env файлу з .env.docker...
    copy .env.docker .env
    echo ⚠️  УВАГА: Відредагуйте .env файл та додайте ваш OPENAI_API_KEY!
    echo    Файл: .env
)

REM Зупинка існуючих контейнерів
echo 🛑 Зупинка існуючих контейнерів...
docker-compose down

REM Видалення старих образів для пересборки
echo 🧹 Очищення старих образів...
docker-compose rm -f backend

REM Збірка та запуск сервісів
echo 🏗️  Збірка та запуск сервісів...
docker-compose up --build -d db redis

REM Очікування запуску бази даних
echo ⏳ Очікування запуску PostgreSQL...
timeout /t 10 /nobreak > nul

REM Запуск бекенду
echo 🔧 Запуск бекенду...
docker-compose up --build -d backend

REM Запуск Adminer для розробки
echo 🗄️  Запуск Adminer для управління БД...
docker-compose --profile dev up -d adminer

echo ✅ Розгортання завершено!
echo.
echo 📊 Доступні сервіси:
echo    🔗 API документація: http://localhost:8000/docs
echo    🔗 Backend API: http://localhost:8000
echo    🔗 Adminer (БД): http://localhost:8080
echo    🔗 Health Check: http://localhost:8000/health
echo.
echo 📝 Для перегляду логів: docker-compose logs -f backend
echo 🛑 Для зупинки: docker-compose down

pause