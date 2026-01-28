# Smart Email Advisor - Makefile

# Кольори для виводу
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

.PHONY: help dev prod stop clean logs shell test

# Default target
help: ## Показати доступні команди
	@echo "$(GREEN)Smart Email Advisor - Доступні команди:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

dev: ## Запустити в режимі розробки
	@echo "$(GREEN)🚀 Запуск для розробки...$(NC)"
	@if [ ! -f .env ]; then cp .env.docker .env; echo "$(YELLOW)⚠️  Відредагуйте .env файл!$(NC)"; fi
	docker-compose down
	docker-compose up --build -d db redis
	@echo "$(YELLOW)⏳ Очікування БД...$(NC)"
	@sleep 10
	docker-compose up --build -d backend
	docker-compose --profile dev up -d adminer
	@echo "$(GREEN)✅ Готово! API: http://localhost:8000/docs$(NC)"

prod: ## Запустити в режимі продакшену
	@echo "$(GREEN)🚀 Запуск для продакшену...$(NC)"
	@if [ ! -f .env ]; then echo "$(RED)❌ .env файл не знайдено!$(NC)"; exit 1; fi
	docker-compose down
	docker-compose --profile production up --build -d
	@echo "$(GREEN)✅ Готово! Сайт: http://localhost$(NC)"

stop: ## Зупинити всі сервіси
	@echo "$(YELLOW)🛑 Зупинка сервісів...$(NC)"
	docker-compose down

clean: ## Повне очищення (контейнери, образи, volumes)
	@echo "$(RED)🧹 Повне очищення...$(NC)"
	docker-compose down -v --remove-orphans
	docker-compose rm -f
	docker system prune -f
	@echo "$(GREEN)✅ Очищення завершено$(NC)"

logs: ## Показати логи всіх сервісів
	docker-compose logs -f

logs-backend: ## Показати логи бекенду
	docker-compose logs -f backend

logs-db: ## Показати логи бази даних
	docker-compose logs -f db

shell: ## Зайти в shell бекенду
	docker-compose exec backend /bin/bash

shell-db: ## Зайти в PostgreSQL shell
	docker-compose exec db psql -U postgres -d smart_email_advisor

test: ## Запустити тести
	docker-compose exec backend python -m pytest

build: ## Пересібрати образи
	docker-compose build --no-cache

restart: ## Перезапустити сервіси
	docker-compose restart

status: ## Показати статус сервісів
	docker-compose ps

update: ## Оновити залежності
	docker-compose pull
	docker-compose up --build -d

backup-db: ## Створити backup бази даних
	@mkdir -p backups
	docker-compose exec -T db pg_dump -U postgres smart_email_advisor > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup створено в папці backups/$(NC)"

restore-db: ## Відновити базу даних з backup (використання: make restore-db FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then echo "$(RED)❌ Використання: make restore-db FILE=backup.sql$(NC)"; exit 1; fi
	docker-compose exec -T db psql -U postgres -d smart_email_advisor < $(FILE)
	@echo "$(GREEN)✅ База даних відновлена$(NC)"

deploy: ## Deploy to AWS EC2 (використання: make deploy HOST=ubuntu@54.123.45.67)
	@if [ -z "$(HOST)" ]; then echo "$(RED)❌ Використання: make deploy HOST=ubuntu@YOUR_ELASTIC_IP$(NC)"; echo "$(YELLOW)   Або використайте напряму: ./deploy.sh ubuntu@YOUR_ELASTIC_IP$(NC)"; exit 1; fi
	@echo "$(GREEN)🚀 Deploying to AWS EC2...$(NC)"
	./deploy.sh $(HOST)

deploy-all: ## Deploy infrastructure + application (повний деплой)
	@echo "$(GREEN)🚀 Deploying infrastructure and application...$(NC)"
	./deploy-all.sh

deploy-infra: ## Deploy only infrastructure (тільки інфраструктура)
	@echo "$(GREEN)🚀 Deploying infrastructure only...$(NC)"
	cd terraform && terraform init && terraform apply

destroy-infra: ## Destroy infrastructure (видалити інфраструктуру)
	@echo "$(RED)⚠️  Destroying infrastructure...$(NC)"
	cd terraform && terraform destroy