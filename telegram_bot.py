#!/usr/bin/env python3
"""
Telegram Bot с интеграцией MCP сервера и Ollama
Использует logic из interactive_chat.py для работы через Telegram
"""

import json
import asyncio
import os
import logging
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ContextTypes, 
    filters
)
from test_client import MCPTestClient

# Загрузка переменных окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class OllamaIntegration:
    """Интеграция с локальным Ollama для tool calling"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b-instruct-q5_K_M"):
        self.base_url = base_url
        self.model = model
    
    def check_ollama_availability(self) -> bool:
        """Проверка доступности Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def chat_with_tools(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Отправка запроса в Ollama с инструментами"""
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            
            if tools:
                payload["tools"] = tools
            
            response = requests.post(
                f"{self.base_url}/api/chat", 
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": f"Ошибка запроса: {e}"}


class TelegramMCPBot:
    """Telegram Bot с интеграцией MCP сервера и Ollama"""
    
    def __init__(self, token: str):
        self.token = token
        self.mcp_client = MCPTestClient(["python3", "mcp_server.py"])
        self.ollama = OllamaIntegration()
        self.available_tools = []
        
        # Словарь для хранения истории разговоров по пользователям
        self.user_conversations = {}
        
        # Словарь для отслеживания режима отладки пользователей
        self.user_debug_mode = {}
        
        # Создаем приложение
        self.application = Application.builder().token(token).build()
        
    async def start_bot(self):
        """Запуск бота"""
        logger.info("🤖 Запуск Telegram Bot с MCP + Ollama интеграцией")
        
        # Проверка Ollama
        if not self.ollama.check_ollama_availability():
            logger.error("❌ Ollama недоступен! Запустите: ollama serve")
            return False
        
        logger.info("✅ Ollama подключен!")
        
        # Запуск MCP сервера
        try:
            await self.mcp_client.start_server()
            await self.mcp_client.initialize()
            self.available_tools = await self.mcp_client.list_tools()
            logger.info(f"✅ MCP сервер запущен с {len(self.available_tools)} инструментами")
            
            # Регистрируем обработчики
            self.register_handlers()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска MCP: {e}")
            return False
    
    def register_handlers(self):
        """Регистрация обработчиков команд и сообщений"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("tools", self.cmd_tools))
        self.application.add_handler(CommandHandler("slots", self.cmd_slots))
        self.application.add_handler(CommandHandler("plan", self.cmd_plan))
        self.application.add_handler(CommandHandler("search", self.cmd_search))
        self.application.add_handler(CommandHandler("history", self.cmd_history))
        self.application.add_handler(CommandHandler("clear", self.cmd_clear))
        self.application.add_handler(CommandHandler("debug", self.cmd_debug))
        self.application.add_handler(CommandHandler("meet", self.cmd_meet))
        
        # Callback query для inline кнопок
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Обработчик всех текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
    
    def get_user_conversation(self, user_id: int) -> List[Dict]:
        """Получить историю разговора пользователя"""
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = []
        return self.user_conversations[user_id]
    
    def add_to_conversation(self, user_id: int, role: str, content: str):
        """Добавить сообщение в историю разговора"""
        conversation = self.get_user_conversation(user_id)
        conversation.append({"role": role, "content": content})
        
        # Ограничиваем историю до 20 сообщений
        if len(conversation) > 20:
            self.user_conversations[user_id] = conversation[-20:]
    
    def is_debug_mode(self, user_id: int) -> bool:
        """Проверить режим отладки для пользователя"""
        return self.user_debug_mode.get(user_id, False)
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user_id = update.effective_user.id
        
        welcome_text = """🤖 **Добро пожаловать в Корпоративного Помощника!**

Я могу помочь вам с:
• 📅 Планированием встреч и проверкой слотов
• 📋 Поиском по корпоративным регламентам
• 🚀 Просмотром планов развития
• 💬 Ответами на любые вопросы

**Доступные команды:**
/help - показать справку
/tools - список MCP инструментов
/slots - доступные временные слоты
/plan - план развития
/search <запрос> - поиск по регламентам
/meet <дата> <время> <название> - запланировать встречу
/history - история разговора
/clear - очистить историю
/debug - переключить режим отладки

Просто задайте любой вопрос! 🚀"""
        
        # Создаем inline keyboard с быстрыми действиями
        keyboard = [
            [
                InlineKeyboardButton("📅 Слоты", callback_data="quick_slots"),
                InlineKeyboardButton("🚀 План", callback_data="quick_plan")
            ],
            [
                InlineKeyboardButton("🔧 Инструменты", callback_data="quick_tools"),
                InlineKeyboardButton("❓ Справка", callback_data="quick_help")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """📋 **СПРАВКА ПО КОМАНДАМ:**

**Основные команды:**
• `/help` - показать эту справку
• `/tools` - показать доступные MCP инструменты
• `/slots` - показать доступные временные слоты
• `/plan` - показать план развития
• `/search <запрос>` - поиск по регламентам
• `/meet <дата> <время> <название>` - запланировать встречу
• `/history` - показать историю разговора
• `/clear` - очистить историю
• `/debug` - переключить режим отладки

**Примеры использования:**
• `/search отпуск` - найти информацию об отпусках
• `/meet 2024-01-19 14:00 Встреча с командой` - запланировать встречу

**Режим отладки:** {debug_status}

💬 **Или просто задайте любой вопрос!**
Я отвечу используя доступные корпоративные данные."""
        
        user_id = update.effective_user.id
        debug_status = "ВКЛЮЧЕН ✅" if self.is_debug_mode(user_id) else "ВЫКЛЮЧЕН ❌"
        
        await update.message.reply_text(
            help_text.format(debug_status=debug_status),
            parse_mode='Markdown'
        )
    
    async def cmd_tools(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /tools"""
        tools_text = "🔧 **ДОСТУПНЫЕ MCP ИНСТРУМЕНТЫ:**\n\n"
        for i, tool in enumerate(self.available_tools, 1):
            tools_text += f"{i}. **{tool['name']}**\n   📝 {tool['description']}\n\n"
        
        await update.message.reply_text(tools_text, parse_mode='Markdown')
    
    async def cmd_slots(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /slots"""
        try:
            result = await self.mcp_client.call_tool("get_available_slots")
            data = json.loads(result["content"][0]["text"])
            
            slots_text = "📅 **ДОСТУПНЫЕ ВРЕМЕННЫЕ СЛОТЫ:**\n\n"
            for slot in data["available_slots"]:
                times = ", ".join(slot['available_times'])
                slots_text += f"**{slot['date']}:** {times}\n"
            
            await update.message.reply_text(slots_text, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения слотов: {e}")
    
    async def cmd_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /plan"""
        try:
            result = await self.mcp_client.call_tool("get_development_plan")
            data = json.loads(result["content"][0]["text"])
            
            plan_text = f"""🚀 **ПЛАН РАЗВИТИЯ:**

**Текущий уровень:** {data['current_level']}
**Целевой уровень:** {data['target_level']}

**Навыки для развития:**
"""
            for skill in data["skills_to_develop"]:
                plan_text += f"• **{skill['skill']}** ({skill['current_level']} → {skill['target_level']})\n"
            
            await update.message.reply_text(plan_text, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения плана: {e}")
    
    async def cmd_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /search"""
        if not context.args:
            await update.message.reply_text(
                "❌ **Использование:** `/search <запрос>`\n"
                "**Пример:** `/search отпуск`",
                parse_mode='Markdown'
            )
            return
        
        query = " ".join(context.args)
        try:
            result = await self.mcp_client.call_tool("search_regulations", {"query": query})
            data = json.loads(result["content"][0]["text"])
            
            if data.get('results'):
                search_text = f"🔍 **РЕЗУЛЬТАТЫ ПОИСКА ПО '{query}':**\n\n"
                for res in data['results']:
                    search_text += f"❓ **{res['question']}**\n"
                    search_text += f"💡 {res['answer']}\n\n"
                await update.message.reply_text(search_text, parse_mode='Markdown')
            else:
                await update.message.reply_text(
                    f"❌ По запросу '{query}' ничего не найдено\n"
                    "💡 Попробуйте: отпуск, больничный, дресс-код, удаленка"
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка поиска: {e}")
    
    async def cmd_meet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /meet"""
        if len(context.args) < 3:
            await update.message.reply_text(
                "❌ **Использование:** `/meet <дата> <время> <название>`\n"
                "**Пример:** `/meet 2024-01-19 14:00 Встреча с командой`",
                parse_mode='Markdown'
            )
            return
        
        date = context.args[0]
        time = context.args[1]
        title = " ".join(context.args[2:])
        
        try:
            result = await self.mcp_client.call_tool("schedule_meeting", {
                "date": date,
                "time": time,
                "title": title
            })
            data = json.loads(result["content"][0]["text"])
            
            if data["success"]:
                await update.message.reply_text(f"✅ {data['message']}")
            else:
                message = f"❌ {data['message']}"
                if data.get('available_alternatives'):
                    alternatives = ", ".join(data['available_alternatives'])
                    message += f"\n💡 Доступные варианты: {alternatives}"
                await update.message.reply_text(message)
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка планирования: {e}")
    
    async def cmd_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /history"""
        user_id = update.effective_user.id
        conversation = self.get_user_conversation(user_id)
        
        if not conversation:
            await update.message.reply_text("📜 История разговора пуста")
            return
        
        history_text = "📜 **ИСТОРИЯ РАЗГОВОРА (последние 10):**\n\n"
        for i, msg in enumerate(conversation[-10:], 1):
            role_emoji = "👤" if msg['role'] == 'user' else "🤖"
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            history_text += f"{i}. {role_emoji} {content}\n"
        
        await update.message.reply_text(history_text, parse_mode='Markdown')
    
    async def cmd_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /clear"""
        user_id = update.effective_user.id
        self.user_conversations[user_id] = []
        await update.message.reply_text("🧹 История очищена!")
    
    async def cmd_debug(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /debug"""
        user_id = update.effective_user.id
        current_debug = self.is_debug_mode(user_id)
        self.user_debug_mode[user_id] = not current_debug
        
        status = "ВКЛЮЧЕН ✅" if not current_debug else "ВЫКЛЮЧЕН ❌"
        info = "Теперь вы будете видеть какие MCP инструменты использует AI" if not current_debug else "Отладочная информация скрыта"
        
        await update.message.reply_text(
            f"🔍 **Режим отладки:** {status}\n{info}",
            parse_mode='Markdown'
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов от inline кнопок"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "quick_slots":
            await self.cmd_slots(update, context)
        elif data == "quick_plan":
            await self.cmd_plan(update, context)
        elif data == "quick_tools":
            await self.cmd_tools(update, context)
        elif data == "quick_help":
            await self.cmd_help(update, context)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик обычных текстовых сообщений"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        if self.is_debug_mode(user_id):
            await update.message.reply_text("🔍 Анализирую ваш вопрос...")
        else:
            await update.message.reply_text("🤔 Обрабатываю ваш вопрос...")
        
        # Добавляем вопрос в историю
        self.add_to_conversation(user_id, "user", message_text)
        
        try:
            # Получаем ответ через Ollama и MCP
            response = await self.process_with_ollama(user_id, message_text)
            
            # Добавляем ответ в историю
            self.add_to_conversation(user_id, "assistant", response)
            
            # Отправляем ответ пользователю - убираем parse_mode для безопасности
            try:
                await update.message.reply_text(response, parse_mode='Markdown')
            except Exception as markdown_error:
                # Если Markdown не работает, отправляем как обычный текст
                logger.warning(f"Markdown ошибка: {markdown_error}")
                await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(f"❌ Произошла ошибка: {e}")
    
    async def process_with_ollama(self, user_id: int, question: str) -> str:
        """Обработка вопроса через Ollama с MCP инструментами"""
        debug_mode = self.is_debug_mode(user_id)
        
        if debug_mode:
            logger.info(f"🔧 Получаю список доступных MCP инструментов...")
        
        # Преобразуем MCP инструменты в формат Ollama
        mcp_tools = await self.mcp_client.list_tools()
        ollama_tools = []
        for tool in mcp_tools:
            ollama_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                }
            }
            ollama_tools.append(ollama_tool)
        
        if debug_mode:
            tools_list = [tool['function']['name'] for tool in ollama_tools]
            logger.info(f"✅ Преобразовано {len(ollama_tools)} инструментов: {', '.join(tools_list)}")
        
        # Подготавливаем сообщения
        messages = [
            {
                "role": "system", 
                "content": self.build_system_prompt()
            }
        ]
        
        # Добавляем историю разговора (последние 6 сообщений)
        conversation = self.get_user_conversation(user_id)
        if conversation:
            messages.extend(conversation[-6:])
        
        if debug_mode:
            logger.info("🤖 Отправляю запрос в Ollama с tool calling...")
        
        # Отправляем запрос в Ollama
        response = self.ollama.chat_with_tools(messages, ollama_tools)
        
        if "error" in response:
            return f"❌ Ошибка Ollama: {response['error']}"
        
        # Обрабатываем ответ
        assistant_message = response["message"]
        
        # Проверяем наличие tool calls
        if assistant_message.get("tool_calls"):
            return await self.handle_tool_calls_response(assistant_message, messages, ollama_tools, debug_mode)
        else:
            final_response = assistant_message.get("content", "")
            if debug_mode:
                logger.info("ℹ️ Модель не вызвала инструменты")
            return final_response
    
    async def handle_tool_calls_response(self, assistant_message: Dict, messages: List[Dict], ollama_tools: List[Dict], debug_mode: bool) -> str:
        """Обработка вызовов инструментов"""
        tool_calls = assistant_message["tool_calls"]
        
        if debug_mode:
            tools_list = [tool_call["function"]["name"] for tool_call in tool_calls]
            logger.info(f"🔧 Модель вызвала {len(tool_calls)} инструментов: {', '.join(tools_list)}")
        
        # Добавляем сообщение ассистента с tool calls
        messages.append({
            "role": "assistant",
            "content": assistant_message.get("content", ""),
            "tool_calls": tool_calls
        })
        
        # Выполняем каждый tool call
        for tool_call in tool_calls:
            function = tool_call["function"]
            tool_name = function["name"]
            tool_args = function["arguments"]
            
            try:
                if debug_mode:
                    logger.info(f"📞 Выполняю {tool_name}...")
                
                result = await self.mcp_client.call_tool(tool_name, tool_args)
                tool_result = result["content"][0]["text"]
                
                if debug_mode:
                    logger.info(f"✅ Результат: {tool_result[:100]}...")
                
                messages.append({
                    "role": "tool",
                    "content": tool_result
                })
                
            except Exception as e:
                error_msg = f"Ошибка выполнения {tool_name}: {e}"
                if debug_mode:
                    logger.error(f"❌ {error_msg}")
                
                messages.append({
                    "role": "tool", 
                    "content": error_msg
                })
        
        # Отправляем второй запрос с результатами tool calls
        if debug_mode:
            logger.info("🔄 Отправляю результаты инструментов обратно в модель...")
        
        final_response = self.ollama.chat_with_tools(messages, ollama_tools)
        
        if "error" in final_response:
            return f"❌ Ошибка финального запроса: {final_response['error']}"
            
        return final_response["message"].get("content", "")
    
    def build_system_prompt(self) -> str:
        """Строим системный промпт"""
        return """You are a helpful corporate assistant. You have access to several tools that help you answer user questions.

AVAILABLE TOOLS: When you need data to answer a question, you MUST use the available tools. Never provide made-up information.

IMPORTANT: Always use the tools when they can provide the information needed to answer the user's question. Don't just describe the tools - actually use them.

Rules:
- If the user asks about time slots or schedule → use get_available_slots
- If the user wants to schedule a meeting → use schedule_meeting
- If the user asks about regulations or policies → use search_regulations  
- If the user asks about development plans → use get_development_plan

Always respond in Russian after using the tools. Format your response clearly with emojis, but avoid complex Markdown formatting that might break. Use simple formatting only.

Example: If user asks "Покажи доступные слоты", you should call get_available_slots tool, then provide the results in Russian with clear formatting."""
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик ошибок"""
        logger.error(msg="Exception while handling an update:", exc_info=context.error)
        
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                '❌ Произошла ошибка при обработке вашего запроса. Попробуйте еще раз.'
            )
    
    async def run(self):
        """Основной метод запуска бота"""
        try:
            # Инициализируем MCP
            if not await self.start_bot():
                return
            
            logger.info("🚀 Telegram Bot запущен и готов к работе!")
            
            # Запускаем бота - используем async polling вместо run_polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            # Ждем бесконечно, пока не будет прерывания
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                pass
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            # Останавливаем бота
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            except Exception as e:
                logger.warning(f"Ошибка при остановке приложения: {e}")
            
            # Остановка MCP сервера при завершении
            await self.mcp_client.stop_server()
            logger.info("🛑 Telegram Bot остановлен")


async def main():
    """Главная функция"""
    # Получаем токен из переменной окружения
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        logger.error("❌ TELEGRAM_TOKEN не найден в переменных окружения!")
        logger.error("Установите токен: export TELEGRAM_TOKEN='your_bot_token_here'")
        return
    
    # Создаем и запускаем бота
    bot = TelegramMCPBot(token)
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("👋 Получен сигнал завершения. До свидания!")


if __name__ == "__main__":
    asyncio.run(main()) 