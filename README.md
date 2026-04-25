# Register Bot

Telegram-бот для приёма заявок и синхронизации с Google Sheets.

## Возможности

- Создание заявок в личных сообщениях
- Отправка заявок в рабочий чат
- Назначение/смена исполнителя
- Завершение и отмена заявок
- Редактирование заявок
- История изменений в отдельном листе
- Цвет строк по статусу

## Настройка

### 1. Google Таблица

Создайте таблицу с двумя листами:

- `requests` — основной лист для заявок
- `history` — история изменений

Скопируйте `SPREADSHEET_KEY` из URL (часть между `/d/` и `/edit`).

### 2. Google Cloud

1. Включите **Google Sheets API** и **Google Drive API**
2. Создайте сервисный аккаунт
3. Скачайте JSON-ключ
4. Дайте аккаунту доступ к таблице (минимум Editor)

### 3. Telegram

1. Создайте бота через [@BotFather](https://t.me/BotFather) — получите `BOT_TOKEN`
2. Добавьте бота в рабочую группу
3. Отправьте `/chat_info` в группе — получите `GROUP_CHAT_ID` и `GROUP_TOPIC_ID`

### 4. Переменные окружения

Создайте `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
GROUP_CHAT_ID=-1001234567890
GROUP_TOPIC_ID=
SPREADSHEET_KEY=your_google_sheet_key
WORKSHEET_NAME=requests
HISTORY_WORKSHEET_NAME=history
SERVICE_ACCOUNT_FILE=service-account.json
LOG_LEVEL=INFO
```

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Тесты

```bash
python -m unittest discover -s tests
```

## Безопасность

- **Не коммитьте** `.env`, JSON-ключи, `request_meta.json`
- Храните credentials вне репозитория
- Проверяйте `git status` перед пушем

## Структура

| Файл               | Назначение               |
| ------------------ | ------------------------ |
| `main.py`          | Запуск бота              |
| `handlers_*.py`    | Обработчики команд       |
| `sheets_*.py`      | Работа с Google Sheets   |
| `request_store.py` | Локальные метаданные     |
| `presenters.py`    | Форматирование сообщений |
