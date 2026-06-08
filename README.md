# text-to-sql-bot

Telegram-бот на Python.

## Локальный запуск

**1. Создай `.env` на основе примера**
```bash
cp .env.example .env
```
Впиши токен бота (получить у [@BotFather](https://t.me/BotFather)):
```
BOT_TOKEN=ваш_токен
```

**2. Запусти через Docker**
```bash
docker compose up -d --build
```
 
**3. Или без Docker**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Деплой

Автодеплой настроен через GitHub Actions: при каждом пуше в `main` бот пересобирается и перезапускается на сервере.

### Первоначальная настройка сервера

```bash
# Клонировать репозиторий
git clone https://github.com/<user>/text-to-sql-bot.git ~/projects/text-to-sql-bot

# Создать .env с токеном
echo "BOT_TOKEN=ваш_токен" > ~/projects/text-to-sql-bot/.env
```

### GitHub Secrets

В настройках репозитория (Settings → Secrets → Actions) добавить:

| Секрет | Описание |
|---|---|
| `SERVER_HOST` | IP или домен сервера |
| `SERVER_USER` | Пользователь SSH |
| `SERVER_SSH_KEY` | Приватный SSH-ключ (содержимое `~/.ssh/id_ed25519`) |

### Генерация SSH-ключа для деплоя

```bash
# Создать ключ
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/deploy_key -N ""

# Добавить публичный ключ на сервер
ssh-copy-id -i ~/.ssh/deploy_key.pub user@your-server

# Скопировать приватный ключ в секрет SERVER_SSH_KEY
cat ~/.ssh/deploy_key
```
