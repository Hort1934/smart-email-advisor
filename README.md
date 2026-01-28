# Smart Email Advisor - AI-Powered Email Management

Інтелектуальний помічник для аналізу та управління електронними листами з використанням штучного інтелекту.

## Архітектура

Проект використовує мікросервісну архітектуру з Docker:

### Сервіси

1. **AI Agent** (порт 8001) - Окремий сервіс для обробки LLM запитів
2. **Backend** (порт 8000) - FastAPI бекенд для роботи з фронтендом
3. **Event Bridge** (порт 8002) - Координація подій між сервісами
4. **Frontend** (порт 3000) - React інтерфейс користувача
5. **Database** - PostgreSQL з SQLite fallback
6. **Redis** - Кешування та черги повідомлень
7. **Monitoring** - Prometheus для моніторингу

### AWS Інтеграція

- **Bedrock** - Альтернативний LLM провайдер
- **S3** - Зберігання файлів
- **SES** - Відправка email
- **SNS** - Push сповіщення
- **Lambda** - Serverless обробка

## Швидкий старт

### Розробка

```bash
# Клонувати репозиторій
git clone <repository-url>
cd smart-email-advisor

# Створити .env файл
cp .env.example .env

# Запустити всі сервіси
make dev

# Або використати docker-compose напряму
docker-compose --profile development up -d
```

### Продакшн

```bash
# Запустити продакшн сервіси
make prod

# Або
docker-compose --profile production up -d
```

### AWS EC2 Deployment

#### Option 1: Infrastructure + Application (Single Command)

```bash
# Deploy everything: infrastructure + application
./deploy-all.sh

# Or using Makefile
make deploy-all
```

**This will:**
1. Provision AWS infrastructure (EC2, Elastic IP, Security Group)
2. Deploy application automatically
3. Provide access URL

**Prerequisites:**
1. Configure `terraform/terraform.tfvars` (key pair, SSH key path)
2. Configure `.env.production` (passwords, API keys)
3. AWS CLI configured (`aws configure`)

See [INFRASTRUCTURE.md](INFRASTRUCTURE.md) for complete guide.

#### Option 2: Application Only (Existing Infrastructure)

```bash
# Deploy to existing EC2 instance
./deploy.sh ubuntu@YOUR_ELASTIC_IP

# Or using Makefile
make deploy HOST=ubuntu@YOUR_ELASTIC_IP
```

See [README_DEPLOYMENT.md](README_DEPLOYMENT.md) for details.

## Конфігурація

### Environment Variables

Основні змінні (див. [.env.docker](.env.docker)):

```env
# OpenAI
OPENAI_API_KEY=your-openai-key

# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/smart_email_db
REDIS_URL=redis://redis:6379

# Services
AI_AGENT_URL=http://ai-agent:8001
BACKEND_URL=http://backend:8000
```

### LLM Rules

Правила для AI аналізу знаходяться в [config/llm_rules.json](config/llm_rules.json):

- Priority rules (urgent/high/medium/low)
- Category classification (work/personal/spam/newsletter)
- Sentiment analysis
- Response recommendations

## API Endpoints

### Backend (порт 8000)

```
GET  /health                 - Health check
POST /api/emails/analyze     - Аналіз email
GET  /api/emails/{id}       - Отримати email
GET  /api/analytics/summary  - Аналітика
```

### AI Agent (порт 8001)

```
GET  /health                 - Health check
POST /analyze               - Аналіз email через AI
GET  /rules                 - Отримати правила LLM
POST /rules/reload          - Перезавантажити правила
```

### Event Bridge (порт 8002)

```
GET  /health                 - Health check
POST /events/publish        - Опублікувати подію
GET  /events/stats          - Статистика подій
```

## Розробка

### Структура проекту

```
smart-email-advisor/
├── ai-agent/               # AI Agent сервіс
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── backend/                # FastAPI бекенд
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   ├── Dockerfile
│   └── requirements.txt
├── event-bridge/           # Event координатор
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── config/                 # Конфігурація
│   └── llm_rules.json
├── monitoring/             # Prometheus конфіг
├── docker-compose.yml      # Оркестрація сервісів
├── .env.docker            # Environment змінні
└── Makefile               # Команди розробки
```

### Makefile команди

```bash
make dev           # Запустити development
make prod          # Запустити production
make build         # Збудувати всі образи
make logs          # Переглянути логи
make clean         # Очистити контейнери
make test          # Запустити тести
```

## Моніторинг

- **Prometheus** доступний на http://localhost:9090
- **Health checks** для всіх сервісів
- Логування в structured format
- Метрики Redis та PostgreSQL

## Deployment

### AWS EC2

1. Встановити Docker та Docker Compose
2. Налаштувати IAM ролі для сервісів AWS
3. Завантажити код та конфігурацію
4. Запустити через `docker-compose --profile production up -d`

### Environment Variables для AWS

```env
AWS_IAM_ROLE=arn:aws:iam::account:role/SmartEmailRole
AWS_BEDROCK_ENDPOINT=https://bedrock.region.amazonaws.com
AWS_S3_BUCKET=smart-email-storage
AWS_SES_REGION=us-east-1
```

## Безпека

- JWT аутентифікація
- CORS налаштування
- Environment variables для sensitive data
- AWS IAM ролі замість credentials
- Health check endpoints

## Contributing

1. Fork проект
2. Створити feature branch (`git checkout -b feature/amazing-feature`)
3. Commit зміни (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Створити Pull Request

## License

[MIT License](LICENSE)
