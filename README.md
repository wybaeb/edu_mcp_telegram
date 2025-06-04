# 🎓 Educational MCP Server

## Описание

Демонстрационный MCP (Model Context Protocol) сервер для обучающих целей. Создан для студентов, чтобы показать как работает протокол MCP и как создавать свои серверы.

## 🚀 Возможности

### Доступные инструменты (Tools):

1. **`list_tools`** - Показать список всех доступных инструментов с описанием
2. **`get_available_slots`** - Получить доступные временные слоты на текущую неделю  
3. **`schedule_meeting`** - Запланировать встречу на определенную дату и время
4. **`get_development_plan`** - Получить индивидуальный план развития в компании
5. **`search_regulations`** - Найти информацию по корпоративным регламентам

### Ресурсы (Resources):

- `company://calendar/slots` - Доступные временные слоты для встреч
- `company://development/plan` - Индивидуальный план развития  
- `company://regulations/all` - Корпоративные регламенты и политики

### Промпты (Prompts):

- `career_advice` - Получить совет по карьерному развитию
- `meeting_agenda` - Создать повестку дня для встречи

## 📋 Требования

- Python 3.8+
- Ollama с моделью `mistral:latest` (опционально, для демонстрации LLM интеграции)

## 🛠 Установка и запуск

### 1. Клонирование и настройка

```bash
# Перейти в директорию проекта
cd edu_mcp_telegram

# Создать виртуальную среду
python3 -m venv venv

# Активировать виртуальную среду
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt
```

### 2. Запуск демонстрации

```bash
# Быстрый запуск
./demo.sh

# Или вручную
source venv/bin/activate
python3 test_client.py
```

### 3. Запуск только MCP сервера

```bash
source venv/bin/activate
python3 mcp_server.py
```

## 🤖 Интеграция с Ollama (опционально)

Для демонстрации интеграции с LLM установите Ollama:

```bash
# Установка Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Загрузка модели
ollama pull mistral:latest

# Запуск Ollama сервера
ollama serve
```

## 📁 Структура проекта

```
edu_mcp_telegram/
├── venv/                 # Виртуальная среда Python
├── mcp_server.py        # Основной MCP сервер
├── mcp_types.py         # Типы данных для MCP протокола
├── mock_data.py         # Заглушки данных для демонстрации
├── test_client.py       # Тестовый клиент для демонстрации
├── requirements.txt     # Зависимости Python
├── demo.sh             # Скрипт быстрого запуска
└── README.md           # Этот файл
```

## 🎯 Примеры использования

### Прямое взаимодействие с MCP сервером

```python
import json
import subprocess
import asyncio

# Запуск сервера
process = await asyncio.create_subprocess_exec(
    "python3", "mcp_server.py",
    stdin=asyncio.subprocess.PIPE,
    stdout=asyncio.subprocess.PIPE
)

# Инициализация
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
}

process.stdin.write((json.dumps(request) + "\n").encode())
await process.stdin.drain()

response = await process.stdout.readline()
print(json.loads(response.decode()))
```

### Список инструментов

```json
{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
}
```

### Вызов инструмента

```json
{
    "jsonrpc": "2.0", 
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "schedule_meeting",
        "arguments": {
            "date": "2024-01-17",
            "time": "10:00",
            "title": "Встреча с командой",
            "duration": 60
        }
    }
}
```

## 🧩 Архитектура

### MCP Server (`mcp_server.py`)

Основной класс `MCPServer` реализует:

- **JSON-RPC 2.0** протокол для обмена сообщениями
- **Инициализацию** соединения с клиентом
- **Обработку запросов** к инструментам, ресурсам и промптам
- **Управление ошибками** и валидацию запросов

### Типы данных (`mcp_types.py`)

Определяет структуры данных с использованием Pydantic:

- `Tool` - описание инструмента
- `Resource` - описание ресурса  
- `Prompt` - описание промпта
- `JSONRPCResponse` - формат ответа

### Заглушки данных (`mock_data.py`)

Содержит тестовые данные:

- Календарь встреч
- Доступные временные слоты
- План развития карьеры
- Корпоративные регламенты

## 🎓 Обучающие материалы

### Что демонстрирует этот проект:

1. **Протокол MCP** - как устроен обмен сообщениями между клиентом и сервером
2. **JSON-RPC 2.0** - стандартный протокол для RPC вызовов
3. **Инструменты (Tools)** - как создавать функции, доступные LLM
4. **Ресурсы (Resources)** - как предоставлять данные LLM
5. **Промпты (Prompts)** - как создавать шаблоны для LLM
6. **Интеграция с LLM** - как MCP работает с моделями вроде Ollama

### Вопросы для изучения:

1. Как MCP сервер обрабатывает входящие запросы?
2. Какова структура JSON-RPC сообщений?
3. Как реализованы инструменты и их вызов?
4. Как работает инициализация соединения?
5. Как передаются ошибки в MCP протоколе?

## 🔧 Расширение функциональности

### Добавление нового инструмента:

```python
# В класс MCPServer добавить новый инструмент в self.tools
Tool(
    name="my_new_tool",
    description="Описание нового инструмента",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "Первый параметр"}
        },
        "required": ["param1"]
    }
)

# Добавить обработчик в _handle_call_tool
elif tool_name == "my_new_tool":
    return await self._tool_my_new_tool(arguments)

# Реализовать функцию
async def _tool_my_new_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
    param1 = arguments.get("param1")
    # Ваша логика здесь
    return {
        "content": [
            TextContent(text=f"Результат: {param1}").dict()
        ]
    }
```

## 🐛 Отладка

### Логи сервера

Сервер выводит логи в stderr:

```bash
python3 mcp_server.py 2>server.log
```

### Тестирование отдельных компонентов

```bash
# Тест заглушек данных
python3 -c "from mock_data import *; print(get_available_slots_for_week())"

# Тест типов данных  
python3 -c "from mcp_types import Tool; print(Tool(name='test', description='test', inputSchema={}).dict())"
```

## 📚 Дополнительные ресурсы

- [Официальная документация MCP](https://modelcontextprotocol.io/)
- [Спецификация JSON-RPC 2.0](https://www.jsonrpc.org/specification)
- [Документация Ollama](https://ollama.ai/)
- [Pydantic документация](https://docs.pydantic.dev/)

## 🤝 Контрибьюция

Этот проект создан для обучения. Студенты могут:

1. Добавлять новые инструменты
2. Расширять функциональность
3. Улучшать документацию
4. Создавать дополнительные примеры

## 📄 Лицензия

Проект создан в образовательных целях и может свободно использоваться для обучения. 