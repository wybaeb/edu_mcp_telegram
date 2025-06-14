# Telegram Bot с MCP и Ollama

Этот Telegram Bot основан на логике из `interactive_chat.py` и предоставляет полную функциональность корпоративного помощника через Telegram интерфейс.

## 🚀 Особенности

- **Интеграция с MCP сервером** - использует все корпоративные инструменты
- **Ollama Tool Calling** - интеллектуальное использование инструментов
- **Персональные истории** - каждый пользователь имеет свою историю разговоров
- **Режим отладки** - возможность видеть процесс работы AI
- **Inline клавиатуры** - быстрый доступ к основным функциям
- **Markdown форматирование** - красивые ответы с эмодзи

## 📋 Требования

1. **Python 3.8+**
2. **Ollama** должен быть запущен с моделью `llama3.2:3b-instruct-q5_K_M`
3. **Telegram Bot Token** от @BotFather
4. **Зависимости** из `requirements.txt`

## ⚙️ Установка

1. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

2. **Настройте Ollama:**
```bash
# Запустите Ollama
ollama serve

# Установите модель (в другом терминале)
ollama pull llama3.2:3b-instruct-q5_K_M
```

3. **Создайте Telegram бота:**
   - Напишите @BotFather в Telegram
   - Используйте команду `/newbot`
   - Следуйте инструкциям для создания бота
   - Сохраните полученный токен

4. **Установите переменную окружения:**
```bash
export TELEGRAM_TOKEN="ваш_токен_от_botfather"
```

## 🏃‍♂️ Запуск

```bash
python telegram_bot.py
```

После запуска вы увидите сообщения:
```
✅ Ollama подключен!
✅ MCP сервер запущен с X инструментами
🚀 Telegram Bot запущен и готов к работе!
```

## 💬 Использование

### Команды бота:

- `/start` - приветствие и быстрые кнопки
- `/help` - справка по всем командам
- `/tools` - список доступных MCP инструментов
- `/slots` - показать доступные временные слоты
- `/plan` - показать план развития
- `/search <запрос>` - поиск по корпоративным регламентам
- `/meet <дата> <время> <название>` - запланировать встречу
- `/history` - показать историю разговора
- `/clear` - очистить историю
- `/debug` - переключить режим отладки

### Примеры использования:

**Поиск информации:**
```
/search отпуск
```

**Планирование встречи:**
```
/meet 2024-01-19 14:00 Встреча с командой
```

**Свободные вопросы:**
```
Покажи доступные слоты на завтра
Какие у меня навыки нужно развивать?
Сколько дней отпуска я могу взять?
```

## 🔧 Архитектура

```
TelegramMCPBot
├── OllamaIntegration      # Интеграция с Ollama для AI
├── MCPTestClient          # Клиент для MCP сервера  
├── Command Handlers       # Обработчики команд (/start, /help, etc.)
├── Message Handler        # Обработка обычных сообщений
├── Callback Handler       # Обработка inline кнопок
└── User Management        # История и настройки по пользователям
```

## 🎯 Основные возможности

1. **Персонализация**: каждый пользователь имеет свою историю разговоров и настройки
2. **Tool Calling**: AI автоматически выбирает нужные инструменты для ответа
3. **Режим отладки**: можно видеть какие инструменты использует AI
4. **Inline клавиатуры**: быстрый доступ к основным функциям
5. **Обработка ошибок**: graceful handling всех возможных ошибок

## 🐛 Отладка

Если бот не запускается, проверьте:

1. **Ollama запущен:**
```bash
curl http://localhost:11434/api/tags
```

2. **Модель загружена:**
```bash
ollama list | grep llama3.2
```

3. **Токен установлен:**
```bash
echo $TELEGRAM_TOKEN
```

4. **MCP сервер работает:**
```bash
python mcp_server.py
```

## 📊 Логи

Бот выводит подробные логи:
- ✅ Успешные операции  
- ❌ Ошибки и проблемы
- 🔧 Вызовы MCP инструментов (в debug режиме)
- 📞 Tool calling процесс (в debug режиме)

## 🔒 Безопасность

- Бот работает только с авторизованными пользователями Telegram
- История разговоров хранится только в памяти (пропадает при перезапуске)
- Ограничение истории до 20 сообщений на пользователя
- Все ошибки логируются, но не передаются пользователю

## 🤝 Связь с interactive_chat.py

Telegram бот полностью повторяет функциональность интерактивного чата:

| interactive_chat.py | telegram_bot.py |
|---------------------|-----------------|
| Команды `/help`, `/tools` | Аналогичные команды |
| Режим отладки | Персональный режим отладки |
| История разговоров | Персональная история |
| Tool calling через Ollama | Тот же механизм |
| MCP интеграция | Тот же MCP клиент |

**Преимущества Telegram версии:**
- Мультипользовательский режим
- Персональные настройки и история
- Inline клавиатуры для удобства
- Возможность работать из любого места
- Красивое форматирование сообщений

Теперь ваши корпоративные инструменты доступны в Telegram! 🚀 