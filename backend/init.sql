-- Ініціалізація бази даних для Smart Email Advisor

-- Створення розширень
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Створення індексів для покращення продуктивності
-- (Таблиці будуть створені автоматично через SQLAlchemy)

-- Створення користувача для бекенду (якщо потрібно)
-- CREATE USER email_advisor WITH PASSWORD 'email_advisor_pass';
-- GRANT ALL PRIVILEGES ON DATABASE smart_email_advisor TO email_advisor;