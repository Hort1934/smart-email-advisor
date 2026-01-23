#!/bin/bash

# Smart Email Advisor - Production Deployment Script

echo "🚀 Запуск Smart Email Advisor для продакшену..."

# Перевірка наявності .env файлу
if [ ! -f .env ]; then
    echo "❌ Файл .env не знайдено!"
    echo "   Створіть .env файл на основі .env.docker"
    exit 1
fi

# Перевірка OPENAI_API_KEY
if grep -q "your-openai-api-key-here" .env; then
    echo "❌ OPENAI_API_KEY не налаштований в .env файлі!"
    exit 1
fi

echo "🛑 Зупинка існуючих контейнерів..."
docker-compose down

echo "🧹 Очищення старих образів..."
docker-compose rm -f

echo "🏗️  Збірка production образів..."
docker-compose build --no-cache

echo "🚀 Запуск в production режимі..."
docker-compose --profile production up -d

echo "⏳ Очікування запуску всіх сервісів..."
sleep 30

# Перевірка здоров'я сервісів
echo "🏥 Перевірка здоров'я сервісів..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API працює"
else
    echo "❌ Backend API не відповідає"
fi

echo "✅ Production розгортання завершено!"
echo ""
echo "📊 Доступні сервіси:"
echo "   🔗 Веб-додаток: http://localhost"
echo "   🔗 API: http://localhost/api"
echo "   🔗 API документація: http://localhost/docs"
echo ""
echo "📝 Для перегляду логів: docker-compose logs -f"
echo "🛑 Для зупинки: docker-compose down"