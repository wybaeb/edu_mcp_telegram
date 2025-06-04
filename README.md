# 🎓 Образовательный MCP сервер для студентов

Демонстрационный MCP (Model Context Protocol) сервер для изучения протокола и интеграции с AI моделями.

## 🎯 Что это?

Этот проект - **образовательный пример** MCP сервера, который показывает:
- Как создать MCP сервер с нуля
- Как реализовать различные типы инструментов (tools)
- Как интегрировать MCP с локальными LLM (Ollama)
- Как использовать **стандартное tool calling** в Ollama
- Как работать с mock данными без записи на диск

## ✨ Возможности

### 🔧 MCP Инструменты
- **list_tools** - показать доступные инструменты
- **get_available_slots** - просмотр свободных временных слотов
- **schedule_meeting** - планирование встреч с проверкой доступности  
- **get_development_plan** - получение плана карьерного развития
- **search_regulations** - поиск по корпоративным регламентам

### 🤖 AI Интеграция
- Локальная работа с **Ollama** (mistral:latest)
- **Стандартное tool calling** через Ollama API 
- Интерактивный чат с режимом отладки
- Поддержка conversation history

### 📚 Обучающие материалы
- Подробная документация кода
- Множественные примеры тестирования
- Демонстрация различных режимов работы

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
# Клонируем репозиторий
git clone <repo-url>
cd edu_mcp_telegram

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

### 2. Настройка Ollama
```bash
# Запускаем Ollama сервер
ollama serve

# В другом терминале загружаем модель
ollama pull mistral:latest
```

### 3. Запуск проектов

#### Интерактивный чат (рекомендуется)
```bash
python3 interactive_chat.py
```

#### Тестирование стандартного tool calling
```bash
python3 test_standard_tool_calling.py
```

#### Простая демонстрация
```bash
./demo.sh
```

## 🔍 Tool Calling в Ollama

### Стандартный подход (правильный)

Проект использует **официальный Ollama API** для tool calling:

1. **Отправляем инструменты** в массиве `tools`:
```python
payload = {
    "model": "mistral:latest",
    "messages": [{"role": "user", "content": "Покажи слоты"}],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_available_slots",
                "description": "Get available time slots",
                "parameters": {...}
            }
        }
    ]
}
```

2. **Модель возвращает tool_calls**:
```json
{
    "message": {
        "tool_calls": [
            {
                "function": {
                    "name": "get_available_slots",
                    "arguments": {}
                }
            }
        ]
    }
}
```

3. **Выполняем инструменты и отправляем результаты**:
```python
messages.append({
    "role": "tool",
    "content": tool_result
})

# Отправляем второй запрос с результатами
final_response = ollama.chat_with_tools(messages, tools)
```

### Режим отладки

В интерактивном чате доступен режим отладки (команда `/debug`), который показывает:
- Какие MCP инструменты доступны модели
- Какие tool calls делает модель
- Результаты выполнения инструментов
- Процесс обработки ответов

## 📁 Структура проекта

```
edu_mcp_telegram/
├── mcp_server.py          # Основной MCP сервер
├── mcp_types.py           # Типы данных для MCP
├── mock_data.py           # Mock корпоративные данные
├── test_client.py         # MCP клиент для тестирования
├── interactive_chat.py    # Интерактивный чат с Ollama
├── test_standard_tool_calling.py  # Тест стандартного tool calling
├── simple_test.py         # Простой синхронный тест
├── demo.sh               # Быстрый запуск демо
├── README.md             # Документация
├── requirements.txt      # Python зависимости
└── claude_desktop_config.json  # Конфиг для Claude Desktop
```

## 🎮 Режимы работы

### 1. Интерактивный чат
- Полноценный разговор с AI
- Использование MCP инструментов
- Отладка tool calling
- История разговора

### 2. Программное API
- Прямые вызовы MCP инструментов
- Интеграция в существующие системы
- Автоматизированное тестирование

### 3. Claude Desktop
- Интеграция с Claude Desktop
- Готовый конфиг файл
- Простая настройка

## 🧪 Тестирование

### Полная демонстрация
```bash
python3 test_client.py
```

### Тест tool calling
```bash
python3 test_standard_tool_calling.py
```

### Простой тест
```bash
python3 simple_test.py
```

### Отладка ответов модели
```bash
python3 debug_llm_response.py
```

## 📋 Доступные команды в чате

- `/help` - справка по командам
- `/tools` - список MCP инструментов  
- `/slots` - показать временные слоты
- `/plan` - план развития
- `/meet <дата> <время> <название>` - запланировать встречу
- `/search <запрос>` - поиск регламентов
- `/history` - история разговора
- `/clear` - очистить историю
- `/debug` - переключить режим отладки
- `/exit` - выход

## 🔧 Особенности реализации

### MCP Протокол
- JSON-RPC 2.0 транспорт
- Стандартные типы сообщений
- Правильная обработка ошибок
- Поддержка инициализации и capabilities

### Tool Calling
- Стандартный Ollama API
- Проверка доступности временных слотов
- Валидация входных параметров
- Обработка ошибок выполнения

### Mock Данные
- Реалистичные корпоративные сценарии
- Бронирование с проверкой доступности
- Поиск по ключевым словам
- Без записи на диск

## 🎓 Образовательная ценность

Проект демонстрирует:
1. **MCP архитектуру** - protocol, transport, tools
2. **Tool calling паттерны** - стандартные подходы
3. **Error handling** - правильная обработка ошибок
4. **Mock данные** - тестирование без внешних зависимостей
5. **AI интеграцию** - практическое использование LLM
6. **Отладку** - визуализация процесса работы

## 🤝 Интеграция с другими системами

### Claude Desktop
```json
{
  "mcpServers": {
    "edu-mcp": {
      "command": "python3",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/edu_mcp_telegram"
    }
  }
}
```

### Continue.dev
```json
{
  "mcp": {
    "servers": {
      "edu-mcp": {
        "command": ["python3", "mcp_server.py"]
      }
    }
  }
}
```

## 📝 Требования

- Python 3.8+
- Ollama с моделью mistral:latest
- 1GB свободной памяти для модели
- Доступ к localhost:11434 (Ollama)

## 🐛 Отладка

### Ollama не запускается
```bash
# Проверяем процесс
ps aux | grep ollama

# Запускаем вручную
ollama serve

# Проверяем доступность
curl http://localhost:11434/api/tags
```

### Модель не найдена
```bash
# Загружаем модель
ollama pull mistral:latest

# Проверяем список моделей
ollama list
```

### MCP ошибки
```bash
# Отладка с подробными логами
python3 test_client.py

# Проверка в интерактивном режиме
python3 interactive_chat.py
```

## 🎯 Дальнейшее развитие

Возможные улучшения:
- Поддержка других моделей (GPT-4, Claude)
- Персистентное хранение данных
- Веб интерфейс
- Расширенные корпоративные сценарии
- Интеграция с реальными системами

---

**💡 Совет:** Начните с `interactive_chat.py` для понимания основных возможностей, затем изучите код `mcp_server.py` для понимания архитектуры MCP. 