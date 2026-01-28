# Frontend для Smart Email Advisor

Цей проект містить веб-інтерфейс для моніторингу та керування системою обробки spam листів.

## Технології

- **Next.js 14** - React фреймворк
- **TypeScript** - Типізований JavaScript
- **Tailwind CSS** - CSS фреймворк для стилізації
- **Recharts** - Бібліотека для створення графіків
- **Lucide React** - Набір іконок
- **Axios** - HTTP клієнт для API запитів

## Структура проекту

```
frontend/
├── pages/
│   ├── _app.tsx          # Головний компонент додатку
│   └── index.tsx         # Головна сторінка dashboard
├── components/
│   ├── EmailProcessingDashboard.tsx  # Компонент обробки листів
│   ├── SpamAnalysisStats.tsx         # Статистика та графіки
│   ├── SystemStatus.tsx              # Статус системи
│   └── ProcessingLogs.tsx            # Логи обробки
├── styles/
│   └── globals.css       # Глобальні стилі
└── package.json          # Залежності проекту
```

## Встановлення

1. Перейдіть в директорію frontend:
```bash
cd frontend
```

2. Встановіть залежності:
```bash
npm install
```

3. Створіть файл `.env.local` з налаштуваннями:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Запуск

### Development режим
```bash
npm run dev
```

### Production build
```bash
npm run build
npm run start
```

### Export статичних файлів
```bash
npm run build
```

## Особливості

### Dashboard Компоненти

1. **EmailProcessingDashboard** - основний компонент для:
   - Запуску процесу обробки spam листів
   - Відображення кроків обробки (IMAP → AI → Database)
   - Показу останніх оброблених листів
   - Індикатора реального часу обробки

2. **SpamAnalysisStats** - статистичний компонент з:
   - Загальною кількістю оброблених листів
   - Діаграмою рівнів загроз (високий/середній/низький)
   - Графіком категорій spam (фішинг, реклама, шахрайство)
   - Швидкими метриками

3. **SystemStatus** - моніторинг системи:
   - Статус API сервера
   - Стан IMAP підключення
   - Статус бази даних
   - Активність системи

4. **ProcessingLogs** - журнал подій:
   - Логи обробки в реальному часі
   - Фільтрація за типом (success/warning/error/info)
   - Деталі про оброблені листи
   - Часові мітки

### API Інтеграція

Frontend підключається до backend API:

- `GET /health` - перевірка статусу
- `GET /spam` - отримання spam листів
- `POST /analyze-from-spam` - запуск AI аналізу
- `GET /folders` - перевірка IMAP підключення

### Стилізація

Використовується Tailwind CSS з кастомною палітрою:
- Primary: синя гамма
- Success: зелена гамма  
- Warning: жовта гамма
- Danger: червона гамма

### Responsive дизайн

- Адаптивна верстка для desktop та mobile
- Гридова система для компонентів
- Оптимізовані розміри для різних екранів

## Налаштування

Основні налаштування в файлах:

- `next.config.js` - конфігурація Next.js
- `tailwind.config.js` - налаштування Tailwind
- `tsconfig.json` - конфігурація TypeScript
- `postcss.config.js` - обробка CSS

## Розробка

При додаванні нових компонентів:

1. Створіть файл в `components/`
2. Використовуйте TypeScript інтерфейси
3. Застосовуйте Tailwind класи для стилізації
4. Підключіть до головної сторінки `pages/index.tsx`

## Відладка

Для відладки API підключення:
- Перевірте `NEXT_PUBLIC_API_URL` в `.env.local`
- Переконайтеся що backend запущений
- Відкрийте Developer Tools для перегляду Network запитів

## Продакшн

Для розгортання:
1. Налаштуйте правильний `NEXT_PUBLIC_API_URL`
2. Виконайте `npm run build` 
3. Розгорніть статичні файли з `out/` директорії