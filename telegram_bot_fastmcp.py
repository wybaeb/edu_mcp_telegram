#!/usr/bin/env python3
"""
Educational Telegram Bot with FastMCP Integration
Телеграм бот для обучения студентов с интеграцией FastMCP
"""

import asyncio
import json
import logging
import os
import sys
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import AnyUrl

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables will be loaded from system only.")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ Please set TELEGRAM_TOKEN environment variable")
    logger.error("💡 Create a .env file with: TELEGRAM_TOKEN=your_bot_token_here")
    logger.error("🤖 Get your token from @BotFather on Telegram")
    sys.exit(1)


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


class MCPTelegramBot:
    """Telegram bot with MCP server integration and AI capabilities"""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "mcp_server_fastmcp.py"],
            env=None
        )
        self.user_states = {}  # Store user interaction states for commands
        self.user_conversations = {}  # Store conversation history
        self.user_debug_mode = {}  # Store debug mode for users
        self.ollama = OllamaIntegration()
        self.available_mcp_tools = []
    
    async def initialize_mcp(self) -> bool:
        """Initialize MCP connection and get available tools"""
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    self.available_mcp_tools = [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in tools.tools
                    ]
                    logger.info(f"✅ MCP server initialized with {len(self.available_mcp_tools)} tools")
                    return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP: {e}")
            return False
    
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
    
    def build_system_prompt(self) -> str:
        """Строим системный промпт для AI"""
        return """You are a helpful corporate assistant with access to MCP tools. You understand both Russian and English and always respond in Russian.

CRITICAL: You MUST use the available tools to get real data. NEVER provide made-up information about company policies, schedules, or regulations.

TOOL USAGE RULES:
- For ANY question about time slots, meetings, calendar, расписание, слоты → ALWAYS use get_available_slots first
- For scheduling meetings, планирование встреч → use schedule_meeting with required parameters
- For questions about company policies, regulations, rules, отпуск, больничный, дресс-код, регламенты → ALWAYS use search_regulations
- For career development, план развития, навыки → use get_development_plan
- For listing available tools → use list_tools

TOOL PARAMETERS:
- schedule_meeting: {"date": "YYYY-MM-DD", "time": "HH:MM", "title": "Meeting name", "duration": 60}
  ⚠️ duration MUST be integer (number), title MUST not be empty
- search_regulations: {"query": "search term"}
  ⚠️ query MUST not be empty, use specific keywords like "отпуск", "дресс-код", etc.

EXAMPLES WITH CORRECT PARAMETERS:
✅ For "Запланируй встречу на завтра в 10:00":
   schedule_meeting({"date": "2024-01-16", "time": "10:00", "title": "Планируемая встреча", "duration": 60})

✅ For "Что говорит регламент об отпусках?":
   search_regulations({"query": "отпуск"})

✅ For "Дресс-код компании":
   search_regulations({"query": "дресс-код"})

RESPONSE FORMAT:
- Always use tools when the question relates to company data
- Respond in Russian with clear formatting  
- Use emojis but avoid complex Markdown that might break
- Be helpful and comprehensive based on the tool results

If you can't answer without tools and no relevant tool exists, say so clearly."""
    
    def safe_json_parse(self, text):
        """Safely parse JSON string"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw_text": text}
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> str:
        """Call MCP tool and return formatted result"""
        if arguments is None:
            arguments = {}
        
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    
                    if result.content and len(result.content) > 0:
                        parsed = self.safe_json_parse(result.content[0].text)
                        return json.dumps(parsed, indent=2, ensure_ascii=False)
                    else:
                        return "Нет данных"
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return f"Ошибка при выполнении команды: {str(e)}"
    
    async def read_mcp_resource(self, uri: str) -> str:
        """Read MCP resource and return formatted result"""
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    resource_content = await session.read_resource(AnyUrl(uri))
                    
                    if resource_content.contents and len(resource_content.contents) > 0:
                        parsed = self.safe_json_parse(resource_content.contents[0].text)
                        return json.dumps(parsed, indent=2, ensure_ascii=False)
                    else:
                        return "Нет данных"
        except Exception as e:
            logger.error(f"Error reading MCP resource {uri}: {e}")
            return f"Ошибка при чтении ресурса: {str(e)}"
    
    async def get_mcp_prompt(self, prompt_name: str, arguments: Dict[str, Any] = None) -> str:
        """Get MCP prompt and return formatted result"""
        if arguments is None:
            arguments = {}
        
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    prompt = await session.get_prompt(prompt_name, arguments)
                    
                    if prompt.messages:
                        result = []
                        for i, message in enumerate(prompt.messages):
                            result.append(f"📝 {message.role}: {message.content.text}")
                        return "\n\n".join(result)
                    else:
                        return "Нет промпта"
        except Exception as e:
            logger.error(f"Error getting MCP prompt {prompt_name}: {e}")
            return f"Ошибка при получении промпта: {str(e)}"
    
    def create_main_keyboard(self) -> InlineKeyboardMarkup:
        """Create main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📋 Инструменты", callback_data="tools"),
                InlineKeyboardButton("📚 Ресурсы", callback_data="resources")
            ],
            [
                InlineKeyboardButton("💭 Промпты", callback_data="prompts"),
                InlineKeyboardButton("ℹ️ Помощь", callback_data="help")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def create_tools_keyboard(self) -> InlineKeyboardMarkup:
        """Create tools menu keyboard"""
        keyboard = [
            [InlineKeyboardButton("📋 Список инструментов", callback_data="tool_list_tools")],
            [InlineKeyboardButton("📅 Доступные слоты", callback_data="tool_get_available_slots")],
            [InlineKeyboardButton("📝 Запланировать встречу", callback_data="tool_schedule_meeting")],
            [InlineKeyboardButton("📈 План развития", callback_data="tool_get_development_plan")],
            [InlineKeyboardButton("🔍 Поиск регламентов", callback_data="tool_search_regulations")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def create_resources_keyboard(self) -> InlineKeyboardMarkup:
        """Create resources menu keyboard"""
        keyboard = [
            [InlineKeyboardButton("📅 Календарь", callback_data="resource_calendar")],
            [InlineKeyboardButton("📈 План развития", callback_data="resource_development")],
            [InlineKeyboardButton("📋 Регламенты", callback_data="resource_regulations")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def create_prompts_keyboard(self) -> InlineKeyboardMarkup:
        """Create prompts menu keyboard"""
        keyboard = [
            [InlineKeyboardButton("🎯 Карьерный совет", callback_data="prompt_career_advice")],
            [InlineKeyboardButton("📋 Повестка встречи", callback_data="prompt_meeting_agenda")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # Command handlers
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_text = f"""🤖 **Добро пожаловать в Умного Корпоративного Помощника, {user.first_name}!**

Я понимаю естественный язык и могу помочь вам с:
• 📅 Планированием встреч и проверкой слотов
• 📋 Поиском по корпоративным регламентам
• 🚀 Просмотром планов развития
• 💬 Ответами на любые вопросы

**Просто задайте любой вопрос на русском языке!** 

Примеры:
• "Покажи доступные слоты на завтра"
• "Что говорится об отпусках в регламентах?"
• "Мой план развития"
• "Запланируй встречу на пятницу в 14:00"

**Дополнительные команды:**
/help - справка по командам
/debug - переключить режим отладки
/history - история разговора
/clear - очистить историю

Начинайте общение! 🚀"""
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user_id = update.effective_user.id
        debug_status = "ВКЛЮЧЕН ✅" if self.is_debug_mode(user_id) else "ВЫКЛЮЧЕН ❌"
        
        help_text = f"""📋 **СПРАВКА ПО УМНОМУ ПОМОЩНИКУ:**

**Основной режим работы:**
Просто пишите на естественном языке! Я понимаю русский и автоматически выполню нужные действия.

**Примеры запросов:**
• "Покажи доступные слоты"
• "Что говорится об отпусках?"
• "Мой план развития"
• "Запланируй встречу на завтра в 15:00 по проекту"

**Дополнительные команды:**
• `/help` - эта справка
• `/debug` - режим отладки ({debug_status})
• `/history` - история разговора
• `/clear` - очистить историю
• `/tools` - список доступных инструментов (режим команд)

**Режим команд (вспомогательный):**
Используйте кнопки и команды для структурированного взаимодействия.

💡 **Совет:** Говорите со мной как с обычным помощником!"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def tools_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tools command"""
        await update.message.reply_text(
            "🔧 Выберите инструмент для выполнения:",
            reply_markup=self.create_tools_keyboard()
        )
    
    async def resources_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /resources command"""
        await update.message.reply_text(
            "📚 Выберите ресурс для просмотра:",
            reply_markup=self.create_resources_keyboard()
        )
    
    async def prompts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /prompts command"""
        await update.message.reply_text(
            "💭 Выберите тип промпта:",
            reply_markup=self.create_prompts_keyboard()
        )
    
    async def debug_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle debug mode"""
        user_id = update.effective_user.id
        current_debug = self.is_debug_mode(user_id)
        self.user_debug_mode[user_id] = not current_debug
        
        status = "ВКЛЮЧЕН ✅" if not current_debug else "ВЫКЛЮЧЕН ❌"
        info = "Теперь вы будете видеть как AI использует инструменты" if not current_debug else "Отладочная информация скрыта"
        
        await update.message.reply_text(
            f"🔍 **Режим отладки:** {status}\n{info}",
            parse_mode='Markdown'
        )
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show conversation history"""
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
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear conversation history"""
        user_id = update.effective_user.id
        self.user_conversations[user_id] = []
        await update.message.reply_text("🧹 История очищена!")
    
    # Callback handlers
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        callback_data = query.data
        
        try:
            if callback_data == "main_menu":
                await query.edit_message_text(
                    "🏠 Главное меню\n\nВыберите категорию:",
                    reply_markup=self.create_main_keyboard()
                )
            
            elif callback_data == "tools":
                await query.edit_message_text(
                    "🔧 Инструменты MCP сервера\n\nВыберите инструмент:",
                    reply_markup=self.create_tools_keyboard()
                )
            
            elif callback_data == "resources":
                await query.edit_message_text(
                    "📚 Ресурсы MCP сервера\n\nВыберите ресурс:",
                    reply_markup=self.create_resources_keyboard()
                )
            
            elif callback_data == "prompts":
                await query.edit_message_text(
                    "💭 Промпты MCP сервера\n\nВыберите тип промпта:",
                    reply_markup=self.create_prompts_keyboard()
                )
            
            elif callback_data == "help":
                await self.help_command(update, context)
            
            # Tool handlers
            elif callback_data.startswith("tool_"):
                await self.handle_tool_callback(query, callback_data)
            
            # Resource handlers
            elif callback_data.startswith("resource_"):
                await self.handle_resource_callback(query, callback_data)
            
            # Prompt handlers
            elif callback_data.startswith("prompt_"):
                await self.handle_prompt_callback(query, callback_data, user_id)
            
        except Exception as e:
            logger.error(f"Error in button callback: {e}")
            await query.edit_message_text(f"❌ Произошла ошибка: {str(e)}")
    
    async def handle_tool_callback(self, query, callback_data: str):
        """Handle tool-related callbacks"""
        tool_name = callback_data.replace("tool_", "")
        
        if tool_name in ["list_tools", "get_available_slots", "get_development_plan"]:
            await query.edit_message_text("⏳ Выполняется запрос...")
            result = await self.call_mcp_tool(tool_name)
            
            # Format result for better display
            if tool_name == "list_tools":
                title = "📋 Список доступных инструментов:"
            elif tool_name == "get_available_slots":
                title = "📅 Доступные временные слоты:"
            else:
                title = "📈 План развития:"
            
            formatted_result = f"{title}\n\n```json\n{result}\n```"
            
            # Split long messages
            if len(formatted_result) > 4000:
                await query.edit_message_text(f"{title}\n\n(Результат слишком длинный, отправляю частями...)")
                await query.message.reply_text(f"```json\n{result}\n```", parse_mode='Markdown')
            else:
                await query.edit_message_text(formatted_result, parse_mode='Markdown')
        
        elif tool_name == "search_regulations":
            self.user_states[query.from_user.id] = {"action": "search_regulations"}
            await query.edit_message_text(
                "🔍 Поиск по регламентам\n\nОтправьте поисковый запрос (например: 'отпуск', 'больничный', 'дресс-код'):"
            )
        
        elif tool_name == "schedule_meeting":
            self.user_states[query.from_user.id] = {"action": "schedule_meeting", "step": "date"}
            await query.edit_message_text(
                "📝 Планирование встречи\n\nШаг 1/4: Введите дату встречи в формате YYYY-MM-DD (например: 2024-01-15):"
            )
    
    async def handle_resource_callback(self, query, callback_data: str):
        """Handle resource-related callbacks"""
        resource_map = {
            "resource_calendar": ("company://calendar/slots", "📅 Календарь доступных слотов"),
            "resource_development": ("company://development/plan", "📈 План развития"),
            "resource_regulations": ("company://regulations/all", "📋 Корпоративные регламенты")
        }
        
        if callback_data in resource_map:
            uri, title = resource_map[callback_data]
            await query.edit_message_text("⏳ Загружается ресурс...")
            result = await self.read_mcp_resource(uri)
            
            formatted_result = f"{title}\n\n```json\n{result}\n```"
            
            # Split long messages
            if len(formatted_result) > 4000:
                await query.edit_message_text(f"{title}\n\n(Результат слишком длинный, отправляю частями...)")
                await query.message.reply_text(f"```json\n{result}\n```", parse_mode='Markdown')
            else:
                await query.edit_message_text(formatted_result, parse_mode='Markdown')
    
    async def handle_prompt_callback(self, query, callback_data: str, user_id: int):
        """Handle prompt-related callbacks"""
        if callback_data == "prompt_career_advice":
            self.user_states[user_id] = {"action": "career_advice", "step": "current_role"}
            await query.edit_message_text(
                "🎯 Карьерный совет\n\nШаг 1/2: Введите вашу текущую должность (например: 'Junior Developer'):"
            )
        
        elif callback_data == "prompt_meeting_agenda":
            self.user_states[user_id] = {"action": "meeting_agenda", "step": "meeting_type"}
            await query.edit_message_text(
                "📋 Повестка встречи\n\nШаг 1/2: Введите тип встречи (например: 'ретроспектива команды', 'планирование спринта'):"
            )
    
    async def process_with_ai(self, user_id: int, question: str) -> str:
        """Обработка вопроса через AI с MCP инструментами"""
        debug_mode = self.is_debug_mode(user_id)
        
        if debug_mode:
            logger.info(f"🔧 Обрабатываю вопрос через AI: {question[:50]}...")
        
        # Проверяем доступность Ollama
        if not self.ollama.check_ollama_availability():
            return "❌ AI сервис недоступен. Убедитесь, что Ollama запущен (ollama serve)"
        
        # Преобразуем MCP инструменты в формат Ollama
        ollama_tools = []
        for tool in self.available_mcp_tools:
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
            logger.info(f"✅ Доступно {len(ollama_tools)} инструментов: {', '.join(tools_list)}")
        
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
        
        # Добавляем текущий вопрос
        messages.append({"role": "user", "content": question})
        
        if debug_mode:
            logger.info("🤖 Отправляю запрос в AI...")
        
        # Отправляем запрос в Ollama
        response = self.ollama.chat_with_tools(messages, ollama_tools)
        
        if "error" in response:
            return f"❌ Ошибка AI: {response['error']}"
        
        # Обрабатываем ответ
        assistant_message = response["message"]
        
        # Проверяем наличие tool calls
        if assistant_message.get("tool_calls"):
            return await self.handle_ai_tool_calls(assistant_message, messages, ollama_tools, debug_mode, user_id)
        else:
            final_response = assistant_message.get("content", "")
            if debug_mode:
                logger.info("ℹ️ AI не вызвал инструменты")
                final_response = f"🔍 **DEBUG:** AI не вызвал инструменты, генерирует ответ самостоятельно\n\n{final_response}"
            return final_response if final_response else "🤔 Не смог обработать ваш запрос"
    
    async def handle_ai_tool_calls(self, assistant_message: Dict, messages: List[Dict], ollama_tools: List[Dict], debug_mode: bool, user_id: int) -> str:
        """Обработка вызовов инструментов AI"""
        tool_calls = assistant_message["tool_calls"]
        debug_info = []
        
        if debug_mode:
            tools_list = [tool_call["function"]["name"] for tool_call in tool_calls]
            logger.info(f"🔧 AI вызвал {len(tool_calls)} инструментов: {', '.join(tools_list)}")
            debug_info.append(f"🔧 **DEBUG:** AI вызвал {len(tool_calls)} инструментов: {', '.join(tools_list)}")
        
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
                    logger.info(f"📞 Выполняю {tool_name} с аргументами: {tool_args}")
                    debug_info.append(f"📞 **Выполняю:** {tool_name} с аргументами: `{tool_args}`")
                
                # Исправляем аргументы для schedule_meeting
                if tool_name == "schedule_meeting" and isinstance(tool_args, dict):
                    # Убеждаемся что duration это int
                    if "duration" in tool_args:
                        try:
                            tool_args["duration"] = int(tool_args["duration"]) if tool_args["duration"] else 60
                        except (ValueError, TypeError):
                            tool_args["duration"] = 60
                    else:
                        tool_args["duration"] = 60
                    
                    # Убеждаемся что title не пустой
                    if not tool_args.get("title"):
                        tool_args["title"] = "Запланированная встреча"
                
                result = await self.call_mcp_tool(tool_name, tool_args)
                
                if debug_mode:
                    logger.info(f"✅ Результат {tool_name}: {result[:200]}...")
                    debug_info.append(f"✅ **Результат {tool_name}:** ```{result[:300]}...```")
                
                messages.append({
                    "role": "tool",
                    "content": result
                })
                
            except Exception as e:
                error_msg = f"Ошибка выполнения {tool_name}: {str(e)}"
                full_error = str(e)
                
                if debug_mode:
                    logger.error(f"❌ {error_msg}")
                    logger.error(f"Полная ошибка: {full_error}")
                    debug_info.append(f"❌ **ПОЛНАЯ ОШИБКА {tool_name}:**\n```\n{full_error}\n```")
                
                messages.append({
                    "role": "tool", 
                    "content": error_msg
                })
        
        # Отправляем второй запрос с результатами tool calls
        if debug_mode:
            logger.info("🔄 Отправляю результаты инструментов обратно в AI...")
            debug_info.append("🔄 **Формирую финальный ответ на основе результатов инструментов...**")
        
        final_response = self.ollama.chat_with_tools(messages, ollama_tools)
        
        if "error" in final_response:
            return f"❌ Ошибка финального запроса: {final_response['error']}"
        
        ai_response = final_response["message"].get("content", "🤔 Не смог сформулировать ответ")
        
        # В debug режиме добавляем debug информацию к ответу
        if debug_mode and debug_info:
            debug_section = "\n\n".join(debug_info)
            return f"{debug_section}\n\n---\n\n{ai_response}"
        
        return ai_response

    # Updated text handler - now primary interface
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages as natural language queries (primary interface)"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Check if user is in command state
        if user_id in self.user_states:
            await self.handle_command_flow(update, context)
            return
        
        # Natural language processing (primary mode)
        if self.is_debug_mode(user_id):
            await update.message.reply_text("🔍 Анализирую ваш вопрос...")
        else:
            await update.message.reply_text("🤔 Обрабатываю ваш вопрос...")
        
        # Add to conversation history
        self.add_to_conversation(user_id, "user", text)
        
        try:
            # Process with AI
            response = await self.process_with_ai(user_id, text)
            
            # Add response to history
            self.add_to_conversation(user_id, "assistant", response)
            
            # Send response to user
            try:
                await update.message.reply_text(response, parse_mode='Markdown')
            except Exception as markdown_error:
                # If Markdown fails, send as plain text
                logger.warning(f"Markdown ошибка: {markdown_error}")
                await update.message.reply_text(response)
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(f"❌ Произошла ошибка: {e}")

    async def handle_command_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle command-based interaction flow (auxiliary)"""
        user_id = update.effective_user.id
        text = update.message.text
        
        if user_id not in self.user_states:
            return
        
        state = self.user_states[user_id]
        action = state.get("action")
        
        try:
            if action == "search_regulations":
                await update.message.reply_text("⏳ Ищу информацию...")
                result = await self.call_mcp_tool("search_regulations", {"query": text})
                await update.message.reply_text(f"🔍 Результаты поиска по запросу '{text}':\n\n```json\n{result}\n```", parse_mode='Markdown')
                del self.user_states[user_id]
            
            elif action == "career_advice":
                if state.get("step") == "current_role":
                    state["current_role"] = text
                    state["step"] = "goal"
                    await update.message.reply_text(
                        f"✅ Текущая должность: {text}\n\nШаг 2/2: Введите вашу карьерную цель (например: 'стать Senior Developer'):"
                    )
                elif state.get("step") == "goal":
                    await update.message.reply_text("⏳ Генерирую карьерный совет...")
                    result = await self.get_mcp_prompt("career_advice", {
                        "current_role": state["current_role"],
                        "goal": text
                    })
                    await update.message.reply_text(f"🎯 Карьерный совет:\n\n{result}")
                    del self.user_states[user_id]
            
            elif action == "meeting_agenda":
                if state.get("step") == "meeting_type":
                    state["meeting_type"] = text
                    state["step"] = "participants"
                    await update.message.reply_text(
                        f"✅ Тип встречи: {text}\n\nШаг 2/2: Введите участников (или нажмите /skip для пропуска):"
                    )
                elif state.get("step") == "participants":
                    participants = text if text != "/skip" else "команда"
                    await update.message.reply_text("⏳ Генерирую повестку дня...")
                    result = await self.get_mcp_prompt("meeting_agenda", {
                        "meeting_type": state["meeting_type"],
                        "participants": participants
                    })
                    await update.message.reply_text(f"📋 Повестка дня:\n\n{result}")
                    del self.user_states[user_id]
            
            elif action == "schedule_meeting":
                await self.handle_meeting_scheduling(update, state, text)
        
        except Exception as e:
            logger.error(f"Error handling command flow: {e}")
            await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")
            if user_id in self.user_states:
                del self.user_states[user_id]

    async def handle_meeting_scheduling(self, update: Update, state: Dict, text: str):
        """Handle meeting scheduling flow"""
        user_id = update.effective_user.id
        step = state.get("step")
        
        if step == "date":
            state["date"] = text
            state["step"] = "time"
            await update.message.reply_text(
                f"✅ Дата: {text}\n\nШаг 2/4: Введите время в формате HH:MM (например: 14:00):"
            )
        elif step == "time":
            state["time"] = text
            state["step"] = "title"
            await update.message.reply_text(
                f"✅ Время: {text}\n\nШаг 3/4: Введите название встречи:"
            )
        elif step == "title":
            state["title"] = text
            state["step"] = "duration"
            await update.message.reply_text(
                f"✅ Название: {text}\n\nШаг 4/4: Введите продолжительность в минутах (или нажмите /skip для 60 минут):"
            )
        elif step == "duration":
            duration = 60 if text == "/skip" else int(text) if text.isdigit() else 60
            
            await update.message.reply_text("⏳ Планирую встречу...")
            result = await self.call_mcp_tool("schedule_meeting", {
                "date": state["date"],
                "time": state["time"],
                "title": state["title"],
                "duration": duration
            })
            await update.message.reply_text(f"📝 Результат планирования:\n\n```json\n{result}\n```", parse_mode='Markdown')
            del self.user_states[user_id]
    
    def setup_handlers(self, application: Application):
        """Setup bot handlers"""
        # Command handlers (auxiliary)
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("debug", self.debug_command))
        application.add_handler(CommandHandler("history", self.history_command))
        application.add_handler(CommandHandler("clear", self.clear_command))
        
        # Optional command interface for structured interaction
        application.add_handler(CommandHandler("tools", self.tools_command))
        application.add_handler(CommandHandler("resources", self.resources_command))
        application.add_handler(CommandHandler("prompts", self.prompts_command))
        
        # Callback handlers for command interface
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Primary text message handler for natural language
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))


async def main():
    """Main function"""
    logger.info("🚀 Starting Smart Educational MCP Telegram Bot...")
    
    # Create bot instance
    bot = MCPTelegramBot()
    
    # Initialize MCP server
    logger.info("🔗 Initializing MCP server...")
    if not await bot.initialize_mcp():
        logger.error("❌ Failed to initialize MCP server")
        return
    
    # Check Ollama availability
    logger.info("🤖 Checking AI service...")
    if bot.ollama.check_ollama_availability():
        logger.info("✅ Ollama AI service is available")
    else:
        logger.warning("⚠️ Ollama AI service not available - natural language features will be limited")
        logger.info("💡 To enable AI features, run: ollama serve")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Setup handlers
    bot.setup_handlers(application)
    
    logger.info("✅ Bot is ready! Starting polling...")
    logger.info("💬 Primary mode: Natural language chat")
    logger.info("🔧 Auxiliary mode: Commands and buttons")
    
    try:
        # Manual initialization and start
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Wait indefinitely until interrupted
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pass
            
    except Exception as e:
        logger.error(f"❌ Error during polling: {e}")
        raise
    finally:
        # Stop the bot properly
        try:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
        except Exception as e:
            logger.warning(f"Warning during shutdown: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1) 