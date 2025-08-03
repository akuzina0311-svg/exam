# Руководство по развертыванию

## Локальное развертывание

### Предварительные требования
- Python 3.11+
- Telegram Bot Token
- OpenAI API Key
- PostgreSQL (опционально, по умолчанию SQLite)

### Настройка

1. **Создайте Telegram бота:**
   - Напишите @BotFather в Telegram
   - Выполните команду `/newbot`
   - Сохраните полученный токен

2. **Получите OpenAI API ключ:**
   - Зарегистрируйтесь на https://platform.openai.com
   - Создайте API ключ в разделе API Keys

3. **Настройте переменные окружения:**
```bash
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export OPENAI_API_KEY="your_openai_api_key"
export DATABASE_URL="sqlite:///instance/itmo_bot.db"  # или PostgreSQL URL
```

### Запуск

```bash
# Установите зависимости
pip install -r dependencies.txt

# Запустите веб-приложение
python main.py

# В отдельном терминале запустите бота
python run_bot.py
```

## Развертывание на Replit

1. Форкните проект в Replit
2. Добавьте секреты в Replit Secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `OPENAI_API_KEY`
   - `DATABASE_URL` (для PostgreSQL)
3. Запустите проект - веб-приложение запустится автоматически
4. Для бота запустите `python run_bot.py` в консоли

## Развертывание на Heroku

1. **Подготовка:**
```bash
# Создайте Procfile
echo "web: gunicorn main:app" > Procfile
echo "bot: python run_bot.py" >> Procfile
```

2. **Развертывание:**
```bash
heroku create your-app-name
heroku config:set TELEGRAM_BOT_TOKEN="your_token"
heroku config:set OPENAI_API_KEY="your_key"
heroku addons:create heroku-postgresql:mini
git push heroku main
heroku ps:scale web=1 bot=1
```

## Развертывание на VPS

### С использованием systemd

1. **Создайте сервисы:**

```bash
# /etc/systemd/system/itmo-bot-web.service
[Unit]
Description=ITMO Bot Web Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/itmo-bot
Environment=PATH=/opt/itmo-bot/venv/bin
ExecStart=/opt/itmo-bot/venv/bin/gunicorn --bind 0.0.0.0:5000 main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# /etc/systemd/system/itmo-bot-telegram.service
[Unit]
Description=ITMO Bot Telegram Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/itmo-bot
Environment=PATH=/opt/itmo-bot/venv/bin
ExecStart=/opt/itmo-bot/venv/bin/python run_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

2. **Запуск:**
```bash
sudo systemctl enable itmo-bot-web itmo-bot-telegram
sudo systemctl start itmo-bot-web itmo-bot-telegram
```

## Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY dependencies.txt .
RUN pip install -r dependencies.txt

COPY . .

CMD ["sh", "-c", "python main.py & python run_bot.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://postgres:password@db:5432/itmo_bot
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: itmo_bot
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Мониторинг

Веб-дашборд доступен по адресу приложения и показывает:
- Статистику пользователей
- Историю разговоров
- Информацию о программах
- Метрики активности

## Обслуживание

- Данные о программах обновляются автоматически при запуске
- База данных создается автоматически при первом запуске
- Логи доступны через стандартный вывод приложения