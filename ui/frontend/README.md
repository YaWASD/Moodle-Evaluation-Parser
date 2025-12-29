# Frontend приложение

## Описание

Современный веб-интерфейс для парсера оценочных материалов на React.js или Vue.js.

## Планируемая структура

```
frontend/
├── public/
│   ├── index.html
│   └── assets/
├── src/
│   ├── components/       # React/Vue компоненты
│   │   ├── common/       # Общие компоненты
│   │   ├── file/         # Компоненты работы с файлами
│   │   ├── course/       # Компоненты курсов
│   │   ├── question/     # Компоненты вопросов
│   │   ├── metadata/     # Компоненты метаданных
│   │   ├── document/     # Компоненты документов
│   │   └── statistics/    # Компоненты статистики
│   ├── pages/            # Страницы приложения
│   │   ├── Dashboard.jsx
│   │   ├── FileProcessing.jsx
│   │   ├── Questions.jsx
│   │   ├── Documents.jsx
│   │   └── Statistics.jsx
│   ├── services/         # API клиенты и сервисы
│   │   ├── api.js
│   │   ├── fileService.js
│   │   └── storageService.js
│   ├── hooks/            # Custom hooks (React)
│   │   ├── useFileUpload.js
│   │   ├── useQuestions.js
│   │   └── useDocuments.js
│   ├── store/            # State management (Redux/Vuex)
│   │   ├── slices/
│   │   └── store.js
│   ├── utils/            # Утилиты
│   │   ├── formatters.js
│   │   └── validators.js
│   ├── styles/           # Стили
│   │   ├── main.css
│   │   └── components/
│   ├── App.jsx           # Главный компонент
│   └── index.js          # Точка входа
├── package.json
└── README.md
```

## Основные страницы

### 1. Dashboard (Главная)
- Загрузка файлов (Drag & Drop)
- Быстрая статистика
- Последние операции
- Быстрые действия

### 2. File Processing (Обработка файла)
- Информация о файле
- Список курсов с выбором
- Настройка метаданных
- Предпросмотр вопросов
- Генерация документов

### 3. Questions (Вопросы)
- Таблица всех вопросов
- Редактирование
- Фильтры и поиск
- Массовые операции

### 4. Documents (Документы)
- Список документов
- Предпросмотр
- Скачивание
- Экспорт в другие форматы

### 5. Statistics (Статистика)
- Дашборд с графиками
- Детальная статистика
- Экспорт отчетов

## Технологии

- React.js или Vue.js
- Material-UI / Vuetify для компонентов
- Axios для HTTP запросов
- React-Dropzone / Vue-Dropzone
- Chart.js / Recharts для графиков
- Redux / Vuex для state management
- React Router / Vue Router для навигации

## Компоненты

### FileUpload
Компонент для загрузки файлов с Drag & Drop поддержкой.

### CourseList
Список курсов с чекбоксами, фильтрами и статистикой.

### QuestionTable
Таблица вопросов с возможностью редактирования.

### MetadataForm
Форма для настройки метаданных документа.

### DocumentPreview
Предпросмотр сгенерированного документа.

### StatisticsDashboard
Дашборд со статистикой и графиками.

