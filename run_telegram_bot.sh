#!/bin/bash

# Telegram Bot Launcher Script
# Проверяет все зависимости и запускает бота

echo "🤖 === ЗАПУСК TELEGRAM BOT ==="
echo

# Проверка токена в переменных окружения или .env файле
if [ -z "$TELEGRAM_TOKEN" ]; then
    # Если нет переменной окружения, проверяем .env файл
    if [ -f ".env" ]; then
        # Проверяем есть ли TELEGRAM_TOKEN в .env файле
        if grep -q "TELEGRAM_TOKEN=" .env; then
            echo "✅ TELEGRAM_TOKEN найден в .env файле"
        else
            echo "❌ TELEGRAM_TOKEN не найден ни в переменных окружения, ни в .env файле!"
            echo "   Добавьте в .env файл: echo 'TELEGRAM_TOKEN=your_bot_token_here' >> .env"
            echo "   Или установите переменную: export TELEGRAM_TOKEN='your_bot_token_here'"
            exit 1
        fi
    else
        echo "❌ TELEGRAM_TOKEN не установлен и .env файл не найден!"
        echo "   Создайте .env файл: echo 'TELEGRAM_TOKEN=your_bot_token_here' > .env"
        echo "   Или установите переменную: export TELEGRAM_TOKEN='your_bot_token_here'"
        exit 1
    fi
else
    echo "✅ TELEGRAM_TOKEN найден в переменных окружения"
fi

# Проверка Ollama
echo "🔍 Проверяю Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama недоступен!"
    echo "   Запустите: ollama serve"
    echo "   В новом терминале: ollama pull llama3.2:3b-instruct-q5_K_M"
    exit 1
fi

echo "✅ Ollama доступен"

# Проверка модели
echo "🔍 Проверяю модель llama3.2..."
if ! ollama list | grep -q "llama3.2:3b-instruct-q5_K_M"; then
    echo "❌ Модель llama3.2:3b-instruct-q5_K_M не найдена!"
    echo "   Установите: ollama pull llama3.2:3b-instruct-q5_K_M"
    exit 1
fi

echo "✅ Модель найдена"

# Проверка зависимостей Python
echo "🔍 Проверяю зависимости Python..."
if ! python3 -c "import telegram" > /dev/null 2>&1; then
    echo "❌ python-telegram-bot не установлен!"
    echo "   Установите: pip install -r requirements.txt"
    exit 1
fi

echo "✅ Python зависимости установлены"

# Проверка MCP сервера
echo "🔍 Проверяю MCP сервер..."
if [ ! -f "mcp_server.py" ]; then
    echo "❌ mcp_server.py не найден!"
    echo "   Убедитесь что вы в правильной директории"
    exit 1
fi

echo "✅ MCP сервер найден"

echo
echo "🚀 Все проверки пройдены! Запускаю Telegram Bot..."
echo "   Для остановки нажмите Ctrl+C"
echo "   Логи будут выводиться ниже:"
echo "=" * 50

# Запуск бота
python3 telegram_bot.py 