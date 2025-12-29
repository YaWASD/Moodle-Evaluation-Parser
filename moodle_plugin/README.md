# Moodle плагин: Экспорт оценочных материалов

## Структура плагина

```
moodle_plugin/
├── version.php                    # Версия и метаданные плагина
├── lang/                          # Языковые файлы
│   └── en/
│       └── local_questionexport.php
├── classes/                       # PHP классы
│   ├── api_client.php            # Клиент для Python API
│   ├── template_manager.php      # Управление шаблонами
│   ├── export_manager.php        # Управление экспортом
│   ├── metadata_manager.php      # Управление метаданными
│   └── form/                      # Формы Moodle
│       ├── export_form.php
│       ├── template_form.php
│       └── metadata_form.php
├── forms/                         # Формы (legacy)
│   ├── export_form.php
│   └── template_form.php
├── templates/                     # Mustache шаблоны
│   ├── export_page.mustache
│   ├── templates_page.mustache
│   └── history_page.mustache
├── db/                            # База данных
│   ├── install.xml               # Схема БД
│   └── upgrade.php               # Обновления БД
├── lib.php                        # Основные функции
├── settings.php                   # Настройки плагина
└── README.md                      # Этот файл
```

## Установка

1. Скопируйте папку в `moodle/local/questionexport`
2. Выполните обновление через админ-панель или CLI:
   ```bash
   php admin/cli/upgrade.php
   ```
3. Настройте плагин в `Администрирование → Плагины → Экспорт вопросов`

## Основные компоненты

### API Client (`classes/api_client.php`)

Клиент для взаимодействия с Python REST API сервисом.

**Методы:**
- `export_questions($questions, $format, $template, $metadata)` - экспорт вопросов
- `get_templates()` - получение списка шаблонов
- `get_formats()` - получение списка форматов
- `check_task_status($task_id)` - проверка статуса задачи

### Export Manager (`classes/export_manager.php`)

Управление процессом экспорта вопросов.

**Методы:**
- `get_questions_from_categories($category_ids, $filters)` - получение вопросов
- `prepare_questions_data($questions)` - подготовка данных
- `export($questions, $format, $template, $metadata)` - экспорт
- `save_export_history($export_data)` - сохранение в историю

### Template Manager (`classes/template_manager.php`)

Управление шаблонами оформления.

**Методы:**
- `get_templates($type = null)` - получение шаблонов
- `get_template($id)` - получение шаблона
- `save_template($template_data)` - сохранение шаблона
- `delete_template($id)` - удаление шаблона
- `clone_template($id, $new_name)` - клонирование шаблона

### Metadata Manager (`classes/metadata_manager.php`)

Управление метаданными и шаблонами метаданных.

**Методы:**
- `get_metadata_templates()` - получение шаблонов
- `save_metadata_template($template_data)` - сохранение шаблона
- `apply_template($template_id, $category_id)` - применение шаблона

## База данных

### Таблицы

**local_questionexport_templates**
- id (bigint)
- name (varchar)
- type (varchar)
- config (text, JSON)
- userid (bigint)
- timecreated (bigint)
- timemodified (bigint)

**local_questionexport_metadata**
- id (bigint)
- name (varchar)
- pk_prefix (varchar)
- pk_id (varchar)
- ipk_prefix (varchar)
- ipk_id (varchar)
- description (text)
- userid (bigint)
- timecreated (bigint)

**local_questionexport_exports**
- id (bigint)
- userid (bigint)
- format (varchar)
- template (varchar)
- questions_count (int)
- file_path (varchar)
- file_size (bigint)
- timecreated (bigint)

## Capabilities

- `local/questionexport:export` - экспорт вопросов
- `local/questionexport:managetemplates` - управление шаблонами
- `local/questionexport:viewhistory` - просмотр истории
- `local/questionexport:exportall` - экспорт всех вопросов

## Настройки плагина

В `settings.php`:
- API URL - адрес Python сервиса
- API Timeout - таймаут запросов
- Max file size - максимальный размер файла
- Temp directory - директория для временных файлов

## Разработка

### Добавление нового формата экспорта

1. Добавьте формат в список доступных в `export_manager.php`
2. Обновите форму экспорта
3. Добавьте поддержку в Python API

### Добавление нового типа шаблона

1. Создайте шаблон в `templates/` (JSON)
2. Добавьте поддержку в `template_manager.php`
3. Обновите редактор шаблонов

## Тестирование

```bash
# Запуск тестов
vendor/bin/phpunit local/questionexport/tests/
```

## Лицензия

GPL v3 (совместимо с Moodle)

