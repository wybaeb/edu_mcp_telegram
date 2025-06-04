# Educational MCP Project with FastMCP

## Обзор / Overview

Этот проект демонстрирует использование **официальной библиотеки FastMCP** для создания образовательного MCP (Model Context Protocol) сервера и клиентов. Проект включает в себя MCP сервер, интерактивный чат-клиент, Telegram бота и тестовые клиенты.

This project demonstrates the use of the **official FastMCP library** to create an educational MCP (Model Context Protocol) server and clients. The project includes an MCP server, interactive chat client, Telegram bot, and test clients.

## 🆕 Что нового в FastMCP версии

### Преимущества использования FastMCP:
- ✅ **Официальная библиотека** от создателей MCP протокола
- ✅ **Простота использования** - декораторы `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`
- ✅ **Автоматическая типизация** - FastMCP автоматически генерирует схемы из типов Python
- ✅ **Встроенный lifecycle management** - управление жизненным циклом сервера
- ✅ **Официальная поддержка** и регулярные обновления
- ✅ **Совместимость** с официальным MCP клиентом SDK

### Отличия от самописной реализации:
- 🔄 Использует официальный Python SDK вместо самописного JSON-RPC
- 🔄 Декларативное определение инструментов вместо императивного
- 🔄 Автоматическая генерация схем параметров
- 🔄 Встроенная обработка ошибок и валидация

## 📁 Структура проекта

```
edu_mcp_telegram/
├── mcp_server_fastmcp.py       # 🆕 MCP сервер на FastMCP
├── test_fastmcp_client.py      # 🆕 Тестовый клиент для FastMCP
├── interactive_chat_fastmcp.py # 🆕 Интерактивный чат с FastMCP
├── telegram_bot_fastmcp.py     # 🆕 Telegram бот с FastMCP
├── mock_data.py                # Демо данные (без изменений)
├── pyproject.toml              # Конфигурация проекта с FastMCP
├── requirements.txt            # Старые зависимости
└── README_FastMCP.md           # Эта документация

# Старые файлы (для сравнения):
├── mcp_server.py               # Старый самописный сервер
├── test_client.py              # Старый тестовый клиент
├── interactive_chat.py         # Старый интерактивный чат
├── telegram_bot.py             # Старый Telegram бот
└── mcp_types.py                # Старые типы (больше не нужны)
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Установка uv (если еще не установлен)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Клонирование и настройка проекта
git clone <repository>
cd edu_mcp_telegram

# Установка зависимостей с помощью uv
uv sync
```

### 2. Запуск MCP сервера

```bash
# Запуск FastMCP сервера
uv run python mcp_server_fastmcp.py
```

### 3. Тестирование сервера

```bash
# Автоматические тесты
uv run python test_fastmcp_client.py

# Интерактивный режим
uv run python test_fastmcp_client.py interactive
```

### 4. Интерактивный чат

```bash
uv run python interactive_chat_fastmcp.py
```

### 5. Telegram бот

```bash
# Установите токен бота
export TELEGRAM_BOT_TOKEN="your_bot_token_here"

# Запустите бота
uv run python telegram_bot_fastmcp.py
```

## 🔧 Доступные инструменты (Tools)

| Инструмент | Описание | Параметры |
|------------|----------|-----------|
| `list_tools` | Список всех доступных инструментов | - |
| `get_available_slots` | Доступные временные слоты | - |
| `schedule_meeting` | Планирование встречи | `date`, `time`, `title`, `duration?` |
| `get_development_plan` | План развития сотрудника | - |
| `search_regulations` | Поиск по регламентам | `query` |

## 📚 Доступные ресурсы (Resources)

| URI | Описание |
|-----|----------|
| `company://calendar/slots` | Календарь доступных слотов |
| `company://development/plan` | План развития |
| `company://regulations/all` | Корпоративные регламенты |

## 💭 Доступные промпты (Prompts)

| Промпт | Описание | Параметры |
|--------|----------|-----------|
| `career_advice` | Карьерный совет | `current_role`, `goal` |
| `meeting_agenda` | Повестка встречи | `meeting_type`, `participants?` |

## 📋 Примеры использования

### Использование MCP клиента

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="uv",
    args=["run", "python", "mcp_server_fastmcp.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # Вызов инструмента
        result = await session.call_tool("get_available_slots", {})
        print(result.content[0].text)
        
        # Чтение ресурса
        resource = await session.read_resource(AnyUrl("company://calendar/slots"))
        print(resource.contents[0].text)
        
        # Получение промпта
        prompt = await session.get_prompt("career_advice", {
            "current_role": "Junior Developer",
            "goal": "стать Senior Developer"
        })
        print(prompt.messages[0].content.text)
```

### Создание инструмента в FastMCP

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool()
def calculate_grade(score: float, total: float) -> str:
    """Calculate grade percentage and letter grade"""
    percentage = (score / total) * 100
    letter = "A" if percentage >= 90 else "B" if percentage >= 80 else "C"
    return f"Score: {score}/{total}, Percentage: {percentage:.1f}%, Grade: {letter}"

@mcp.resource("student://profile/{student_id}")
def get_student_profile(student_id: str) -> str:
    """Get student profile as JSON"""
    return json.dumps({"id": student_id, "name": "Student Name"})

@mcp.prompt()
def study_guide(subject: str, topics: str) -> str:
    """Generate study guide prompt"""
    return f"Create a study guide for {subject} covering: {topics}"
```

## 🤖 Telegram бот команды

- `/start` - Главное меню
- `/help` - Справка по командам
- `/tools` - Доступные инструменты
- `/resources` - Доступные ресурсы  
- `/prompts` - Доступные промпты

## 💡 Интерактивный чат команды

```bash
# Системные команды
help        # Справка
status      # Статус подключения
clear       # Очистить экран
quit/exit   # Выход

# MCP команды
tools                                    # Список инструментов
call list_tools                          # Вызвать инструмент
call search_regulations отпуск           # Поиск с параметром
read company://calendar/slots            # Чтение ресурса
prompt career_advice                     # Интерактивный промпт
prompt career_advice "Junior" "Senior"   # Прямой вызов промпта
```

## 🔍 Сравнение реализаций

### Старая самописная реализация:
```python
class MCPServer:
    def __init__(self):
        self.tools = [
            Tool(name="get_slots", description="...", inputSchema={...})
        ]
    
    async def handle_request(self, request):
        if request["method"] == "tools/call":
            # Ручная обработка JSON-RPC
            pass
```

### Новая FastMCP реализация:
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Educational Server")

@mcp.tool()
def get_available_slots() -> str:
    """Получить доступные временные слоты"""
    # Автоматическая типизация и валидация
    return json.dumps(slots_data)

if __name__ == "__main__":
    mcp.run()  # Автоматический запуск сервера
```

## 🛠️ Разработка

### Установка в режиме разработки

```bash
# Установка с dev зависимостями
uv sync --dev

# Запуск линтера
uv run ruff check .
uv run ruff format .

# Запуск тестов
uv run pytest
```

### Добавление нового инструмента

```python
@mcp.tool()
def new_tool(param1: str, param2: int = 42) -> str:
    """Описание нового инструмента
    
    Args:
        param1: Обязательный строковый параметр
        param2: Опциональный числовой параметр
    """
    return f"Result: {param1} with {param2}"
```

### Добавление нового ресурса

```python
@mcp.resource("custom://data/{data_id}")
def get_custom_data(data_id: str) -> str:
    """Получить кастомные данные"""
    return json.dumps({"id": data_id, "data": "..."})
```

### Добавление нового промпта

```python
@mcp.prompt()
def custom_prompt(context: str, task: str) -> str:
    """Кастомный промпт для задач"""
    return f"Given context: {context}\nPlease help with: {task}"
```

## 📚 Дополнительные ресурсы

- [Официальная документация MCP](https://modelcontextprotocol.io/)
- [FastMCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Спецификация MCP](https://spec.modelcontextprotocol.io/)
- [Примеры MCP серверов](https://github.com/modelcontextprotocol/servers)

## 🎓 Обучающие материалы

### Для студентов:
1. **Основы MCP** - изучите `mcp_server_fastmcp.py`
2. **Клиент-серверная архитектура** - посмотрите `test_fastmcp_client.py`
3. **Интеграция с внешними API** - изучите `telegram_bot_fastmcp.py`
4. **Интерактивные приложения** - разберите `interactive_chat_fastmcp.py`

### Практические задания:
1. Добавьте новый инструмент для работы с календарем
2. Создайте ресурс для получения новостей
3. Реализуйте промпт для генерации технического задания
4. Интегрируйте с внешним API (погода, курсы валют)

## 🚨 Troubleshooting

### MCP сервер не запускается
```bash
# Проверьте версию Python
python --version  # Должна быть >= 3.10

# Установите зависимости заново
uv sync --reinstall
```

### Telegram бот не отвечает
```bash
# Проверьте токен
echo $TELEGRAM_BOT_TOKEN

# Проверьте логи
uv run python telegram_bot_fastmcp.py
```

### Ошибки подключения к серверу
```bash
# Убедитесь что сервер запущен в отдельном терминале
uv run python mcp_server_fastmcp.py

# Проверьте доступность портов
ps aux | grep mcp_server
```

## 📝 Changelog

### v2.0.0 (FastMCP Edition)
- ✅ Переход на официальную библиотеку FastMCP
- ✅ Упрощение кода с использованием декораторов
- ✅ Автоматическая типизация и валидация
- ✅ Улучшенная обработка ошибок
- ✅ Новый интерактивный чат клиент
- ✅ Обновленный Telegram бот
- ✅ Comprehensive тестирование

### v1.0.0 (Custom Implementation)
- ✅ Самописная реализация MCP протокола
- ✅ Базовые инструменты и ресурсы
- ✅ Простой Telegram бот
- ✅ Демо данные для тестирования

## 🤝 Контрибьютинг

1. Fork проекта
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект создан в образовательных целях. Свободно используйте для обучения и экспериментов.

---

**Счастливого изучения MCP! 🎓🚀** 