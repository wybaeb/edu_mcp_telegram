#!/bin/bash
echo "🎓 Educational MCP Server Demo"
echo "=============================="
echo

echo "Проверка зависимостей..."
python3 -c "import asyncio, json, requests; print('✅ Все зависимости установлены')" || {
    echo "❌ Устанавливаю зависимости..."
    source venv/bin/activate
    pip install -r requirements.txt
}

echo
echo "Запуск демонстрации..."
source venv/bin/activate
python3 test_client.py
