#!/usr/bin/env python3
"""
Interactive Chat Client for Educational MCP Server using FastMCP
Интерактивный чат-клиент для демонстрационного MCP-сервера с FastMCP
"""

import asyncio
import json
import sys
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import AnyUrl


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
            # Подготавливаем payload согласно документации Ollama
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            
            # Добавляем инструменты если есть
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


class InteractiveMCPChat:
    """Interactive chat interface for MCP server"""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "mcp_server_fastmcp.py"],
            env=None
        )
        self.session = None
        self.read_stream = None
        self.write_stream = None
        self.user_state = {}
        self.ollama = OllamaIntegration()
        self.conversation_history = []
        self.available_tools = []
        self.natural_language_mode = False
        self.verbose_mode = True
    
    def safe_json_parse(self, text):
        """Safely parse JSON string"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw_text": text}
    
    def format_json_output(self, data, title="Результат"):
        """Format JSON data for better display"""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                return f"{title}:\n{data}"
        
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        return f"\n{title}:\n{'='*50}\n{formatted}\n{'='*50}"
    
    async def connect_to_server(self):
        """Connect to MCP server"""
        print("🔗 Подключение к MCP серверу...")
        try:
            self.stdio_client = stdio_client(self.server_params)
            self.read_stream, self.write_stream = await self.stdio_client.__aenter__()
            self.session = ClientSession(self.read_stream, self.write_stream)
            await self.session.__aenter__()
            await self.session.initialize()
            
            # Получаем список доступных инструментов для Ollama
            tools = await self.session.list_tools()
            self.available_tools = []
            for tool in tools.tools:
                tool_dict = {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                }
                self.available_tools.append(tool_dict)
            
            print("✅ Успешно подключились к MCP серверу!")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    async def disconnect_from_server(self):
        """Disconnect from MCP server"""
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
            if hasattr(self, 'stdio_client'):
                await self.stdio_client.__aexit__(None, None, None)
        except Exception as e:
            print(f"Ошибка при отключении: {e}")
    
    def show_welcome(self):
        """Show welcome message"""
        print("""
🎓 Educational MCP Interactive Chat with Natural Language
========================================================

Добро пожаловать в интерактивный чат с MCP сервером на FastMCP!

РЕЖИМЫ РАБОТЫ:
  🤖 Естественный язык (с Ollama) - просто задавайте вопросы
  💻 Командный режим - прямые MCP команды

Системные команды:
  /nlp        - Переключиться в режим естественного языка
  /cmd        - Переключиться в командный режим  
  /debug      - Переключить режим отладки
  help        - Показать справку по командам
  status      - Показать статус подключения
  clear       - Очистить экран
  quit/exit   - Выйти из программы

В командном режиме:
  tools       - Показать доступные инструменты  
  resources   - Показать доступные ресурсы
  prompts     - Показать доступные промпты
  call <tool> [args...]     - Вызвать инструмент
  read <uri>                - Прочитать ресурс
  prompt <name> [args...]   - Получить промпт

В режиме естественного языка:
  - Просто задавайте вопросы: "Покажи доступные слоты"
  - "Запланируй встречу на завтра в 14:00 по проекту"
  - "Найди информацию про отпуск"
  - "Какой у меня план развития?"

Введите команду или вопрос:
        """)
    
    def parse_command(self, command_line: str):
        """Parse command line into command and arguments"""
        parts = command_line.strip().split()
        if not parts:
            return None, []
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        return command, args
    
    async def handle_natural_language_question(self, question: str):
        """Handle natural language question with Ollama"""
        if self.verbose_mode:
            print("🔍 === АНАЛИЗ ВОПРОСА ===")
            print(f"📝 Вопрос: {question}")
        else:
            print("🤔 Обрабатываю ваш вопрос...")
        
        # Добавляем вопрос в историю
        self.conversation_history.append({
            "role": "user",
            "content": question
        })
        
        try:
            # Преобразуем MCP инструменты в формат Ollama
            if self.verbose_mode:
                print("🔧 Получаю список доступных MCP инструментов...")
            
            ollama_tools = []
            for tool in self.available_tools:
                ollama_tool = {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["inputSchema"]
                    }
                }
                ollama_tools.append(ollama_tool)
            
            if self.verbose_mode:
                print(f"✅ Преобразовано {len(ollama_tools)} MCP инструментов в формат Ollama:")
                for tool in ollama_tools:
                    print(f"   • {tool['function']['name']}: {tool['function']['description']}")
                print()
            
            # Подготавливаем сообщения для Ollama
            messages = [
                {
                    "role": "system", 
                    "content": self.build_system_prompt()
                }
            ]
            
            # Добавляем историю разговора (последние 6 сообщений)
            if self.conversation_history:
                messages.extend(self.conversation_history[-6:])
            
            if self.verbose_mode:
                print("🤖 Отправляю запрос в Ollama с tool calling...")
            
            # Отправляем запрос в Ollama
            response = self.ollama.chat_with_tools(messages, ollama_tools)
            
            if "error" in response:
                print(f"❌ Ошибка Ollama: {response['error']}")
                return
            
            # Обрабатываем ответ
            assistant_message = response["message"]
            
            if self.verbose_mode:
                print("📤 Получен ответ от Ollama")
                
            # Проверяем наличие tool calls
            if assistant_message.get("tool_calls"):
                await self.handle_tool_calls(assistant_message, messages, ollama_tools)
            else:
                # Просто выводим ответ модели
                final_response = assistant_message.get("content", "")
                
                if self.verbose_mode:
                    print("ℹ️ Модель не вызвала инструменты")
                    print("=" * 60)
                    
                print(f"🤖 Помощник: {final_response}")
                print()
                
                # Добавляем ответ в историю
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": final_response
                })
                
        except Exception as e:
            print(f"❌ Ошибка обработки вопроса: {e}")
            print()

    async def handle_tool_calls(self, assistant_message: Dict, messages: List[Dict], ollama_tools: List[Dict]):
        """Обработка вызовов инструментов"""
        tool_calls = assistant_message["tool_calls"]
        
        if self.verbose_mode:
            print(f"🔧 Модель вызвала {len(tool_calls)} инструментов:")
            for i, tool_call in enumerate(tool_calls, 1):
                func = tool_call["function"]
                print(f"   {i}. {func['name']} с аргументами: {func['arguments']}")
            print()
        
        # Добавляем сообщение ассистента с tool calls в историю
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
                if self.verbose_mode:
                    print(f"   📞 Выполняю {tool_name}...")
                
                # Вызываем MCP инструмент
                result = await self.session.call_tool(tool_name, tool_args)
                tool_result = result.content[0].text
                
                if self.verbose_mode:
                    print(f"   ✅ Результат: {tool_result[:100]}...")
                
                # Добавляем результат tool call
                messages.append({
                    "role": "tool",
                    "content": tool_result
                })
                
            except Exception as e:
                error_msg = f"Ошибка выполнения {tool_name}: {e}"
                if self.verbose_mode:
                    print(f"   ❌ {error_msg}")
                
                messages.append({
                    "role": "tool", 
                    "content": error_msg
                })
        
        # Отправляем второй запрос с результатами tool calls
        if self.verbose_mode:
            print("\n🔄 Отправляю результаты инструментов обратно в модель...")
        
        final_response = self.ollama.chat_with_tools(messages, ollama_tools)
        
        if "error" in final_response:
            print(f"❌ Ошибка финального запроса: {final_response['error']}")
            return
            
        final_content = final_response["message"].get("content", "")
        
        if self.verbose_mode:
            print("=" * 60)
            
        print(f"🤖 Помощник: {final_content}")
        print()
        
        # Добавляем финальный ответ в историю
        self.conversation_history.append({
            "role": "assistant",
            "content": final_content
        })

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

Always respond in Russian after using the tools.

Example: If user asks "Покажи доступные слоты", you should call get_available_slots tool, then provide the results in Russian."""

    async def handle_tools_command(self, args):
        """Handle tools command"""
        try:
            tools = await self.session.list_tools()
            print(f"\n📋 Доступные инструменты ({len(tools.tools)}):")
            print("=" * 60)
            for tool in tools.tools:
                print(f"🔧 {tool.name}")
                print(f"   📝 {tool.description}")
                if hasattr(tool, 'inputSchema') and tool.inputSchema and 'properties' in tool.inputSchema:
                    params = list(tool.inputSchema['properties'].keys())
                    if params:
                        print(f"   📋 Параметры: {', '.join(params)}")
                print()
        except Exception as e:
            print(f"❌ Ошибка получения списка инструментов: {e}")
    
    async def handle_resources_command(self, args):
        """Handle resources command"""
        try:
            resources = await self.session.list_resources()
            print(f"\n📚 Доступные ресурсы ({len(resources.resources)}):")
            print("=" * 60)
            for resource in resources.resources:
                print(f"📄 {resource.uri}")
                print(f"   📝 {resource.name}")
                if hasattr(resource, 'description') and resource.description:
                    print(f"   📋 {resource.description}")
                print()
        except Exception as e:
            print(f"❌ Ошибка получения списка ресурсов: {e}")
    
    async def handle_prompts_command(self, args):
        """Handle prompts command"""
        try:
            prompts = await self.session.list_prompts()
            print(f"\n💭 Доступные промпты ({len(prompts.prompts)}):")
            print("=" * 60)
            for prompt in prompts.prompts:
                print(f"🎯 {prompt.name}")
                print(f"   📝 {prompt.description}")
                if hasattr(prompt, 'arguments') and prompt.arguments:
                    args_str = ", ".join([f"{arg.name}{'*' if arg.required else ''}" for arg in prompt.arguments])
                    print(f"   📋 Аргументы: {args_str} (* - обязательные)")
                print()
        except Exception as e:
            print(f"❌ Ошибка получения списка промптов: {e}")
    
    async def handle_call_command(self, args):
        """Handle call command"""
        if not args:
            print("❌ Укажите название инструмента. Пример: call list_tools")
            return
        
        tool_name = args[0]
        tool_args = {}
        
        # Parse arguments for specific tools
        if tool_name == "search_regulations" and len(args) > 1:
            tool_args["query"] = " ".join(args[1:])
        elif tool_name == "schedule_meeting":
            if len(args) >= 4:
                tool_args = {
                    "date": args[1],
                    "time": args[2], 
                    "title": " ".join(args[3:])
                }
            else:
                print("❌ Для schedule_meeting нужны аргументы: date time title")
                print("   Пример: call schedule_meeting 2024-01-15 14:00 Планёрка команды")
                return
        
        try:
            print(f"⏳ Выполняется {tool_name}...")
            result = await self.session.call_tool(tool_name, tool_args)
            
            if result.content and len(result.content) > 0:
                parsed = self.safe_json_parse(result.content[0].text)
                print(self.format_json_output(parsed, f"Результат {tool_name}"))
            else:
                print("⚠️ Инструмент выполнился, но не вернул данных")
                
        except Exception as e:
            print(f"❌ Ошибка выполнения инструмента {tool_name}: {e}")
    
    async def handle_read_command(self, args):
        """Handle read command"""
        if not args:
            print("❌ Укажите URI ресурса. Пример: read company://calendar/slots")
            return
        
        uri = args[0]
        try:
            print(f"⏳ Читается ресурс {uri}...")
            resource_content = await self.session.read_resource(AnyUrl(uri))
            
            if resource_content.contents and len(resource_content.contents) > 0:
                parsed = self.safe_json_parse(resource_content.contents[0].text)
                print(self.format_json_output(parsed, f"Содержимое ресурса {uri}"))
            else:
                print("⚠️ Ресурс найден, но не содержит данных")
                
        except Exception as e:
            print(f"❌ Ошибка чтения ресурса {uri}: {e}")
    
    async def handle_prompt_command(self, args):
        """Handle prompt command"""
        if not args:
            print("❌ Укажите название промпта. Пример: prompt career_advice")
            return
        
        prompt_name = args[0]
        prompt_args = {}
        
        # Parse arguments for specific prompts
        if prompt_name == "career_advice" and len(args) >= 3:
            prompt_args = {
                "current_role": args[1],
                "goal": " ".join(args[2:])
            }
        elif prompt_name == "meeting_agenda" and len(args) >= 2:
            prompt_args = {
                "meeting_type": args[1],
                "participants": " ".join(args[2:]) if len(args) > 2 else "команда"
            }
        elif prompt_name in ["career_advice", "meeting_agenda"]:
            # Interactive mode for prompts
            if prompt_name == "career_advice":
                current_role = input("Введите текущую должность: ")
                goal = input("Введите карьерную цель: ")
                prompt_args = {"current_role": current_role, "goal": goal}
            elif prompt_name == "meeting_agenda":
                meeting_type = input("Введите тип встречи: ")
                participants = input("Введите участников (Enter для 'команда'): ") or "команда"
                prompt_args = {"meeting_type": meeting_type, "participants": participants}
        
        try:
            print(f"⏳ Генерируется промпт {prompt_name}...")
            prompt = await self.session.get_prompt(prompt_name, prompt_args)
            
            if prompt.messages:
                print(f"\n💭 Промпт '{prompt_name}':")
                print("=" * 60)
                for i, message in enumerate(prompt.messages, 1):
                    print(f"📝 Сообщение {i} ({message.role}):")
                    print(f"{message.content.text}")
                    print("-" * 40)
            else:
                print("⚠️ Промпт сгенерирован, но не содержит сообщений")
                
        except Exception as e:
            print(f"❌ Ошибка генерации промпта {prompt_name}: {e}")
    
    def handle_status_command(self):
        """Handle status command"""
        status = "✅ Подключен" if self.session else "❌ Отключен"
        mode = "🤖 Естественный язык" if self.natural_language_mode else "💻 Командный"
        debug = "✅ Включен" if self.verbose_mode else "❌ Выключен"
        ollama_status = "✅ Доступен" if self.ollama.check_ollama_availability() else "❌ Недоступен"
        
        print(f"\n📊 Статус системы:")
        print(f"   🔗 MCP сервер: {status}")
        print(f"   🎯 Режим работы: {mode}")
        print(f"   🔍 Режим отладки: {debug}")
        print(f"   🤖 Ollama: {ollama_status}")
        if self.session:
            print(f"   📚 Инструментов: {len(self.available_tools)}")
            print(f"   💬 История: {len(self.conversation_history)} сообщений")
            print(f"   🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def handle_clear_command(self):
        """Handle clear command"""
        import os
        os.system('clear' if os.name == 'posix' else 'cls')
        self.conversation_history.clear()
        print("🧹 Экран и история очищены")
    
    def show_help(self):
        """Show help message"""
        mode_info = "🤖 ЕСТЕСТВЕННЫЙ ЯЗЫК (текущий)" if self.natural_language_mode else "💻 КОМАНДНЫЙ РЕЖИМ (текущий)"
        
        print(f"""
📖 Справка по MCP Interactive Chat
==================================
{mode_info}

🔄 ПЕРЕКЛЮЧЕНИЕ РЕЖИМОВ:
  /nlp                            - Переключиться в режим естественного языка
  /cmd                            - Переключиться в командный режим
  /debug                          - Переключить режим отладки ({self.verbose_mode})

🤖 В РЕЖИМЕ ЕСТЕСТВЕННОГО ЯЗЫКА:
  - Просто задавайте вопросы естественным языком
  - "Покажи доступные слоты на эту неделю"
  - "Запланируй встречу на завтра в 14:00 по проекту X"
  - "Найди информацию про отпуск в регламентах"
  - "Какой у меня план развития?"

💻 В КОМАНДНОМ РЕЖИМЕ:
  tools                           - Показать список доступных инструментов
  call list_tools                 - Показать детальный список инструментов
  call get_available_slots        - Показать доступные временные слоты
  call get_development_plan       - Показать план развития
  call search_regulations <запрос> - Поиск по регламентам
  call schedule_meeting <дата> <время> <название> - Запланировать встречу
  
  Примеры:
    call search_regulations отпуск
    call schedule_meeting 2024-01-15 14:00 Планёрка команды

📚 РЕСУРСЫ (Resources):
  resources                       - Показать список доступных ресурсов
  read company://calendar/slots   - Календарь доступных слотов
  read company://development/plan - План развития
  read company://regulations/all  - Все регламенты

💭 ПРОМПТЫ (Prompts):
  prompts                         - Показать список доступных промптов
  prompt career_advice            - Карьерный совет (интерактивно)
  prompt meeting_agenda           - Повестка встречи (интерактивно)

⚙️ СИСТЕМНЫЕ КОМАНДЫ:
  status                          - Показать статус подключения
  clear                           - Очистить экран и историю
  help                            - Показать эту справку
  quit / exit                     - Выйти из программы

💡 СОВЕТЫ:
• В естественном режиме требуется Ollama (ollama serve)
• Используйте /debug для просмотра работы с инструментами
• В командном режиме используйте кавычки для аргументов с пробелами
        """)
    
    async def run_interactive_loop(self):
        """Run the main interactive loop"""
        while True:
            try:
                mode_indicator = "🤖" if self.natural_language_mode else "💻"
                command_line = input(f"\n{mode_indicator} > ").strip()
                
                if not command_line:
                    continue
                
                # Системные команды работают в любом режиме
                if command_line.startswith('/'):
                    command = command_line[1:].lower()
                    if command in ['quit', 'exit']:
                        print("👋 До свидания!")
                        break
                    elif command == 'nlp':
                        if not self.ollama.check_ollama_availability():
                            print("❌ Ollama недоступен! Запустите: ollama serve")
                            print("И убедитесь что модель llama3.2:3b-instruct-q5_K_M загружена: ollama pull llama3.2:3b-instruct-q5_K_M")
                        else:
                            self.natural_language_mode = True
                            print("🤖 Переключились в режим естественного языка")
                            print("💬 Теперь можете задавать вопросы обычным языком!")
                    elif command == 'cmd':
                        self.natural_language_mode = False
                        print("💻 Переключились в командный режим")
                        print("🔧 Используйте команды: tools, call, read, prompt")
                    elif command == 'debug':
                        self.verbose_mode = not self.verbose_mode
                        status = "ВКЛЮЧЕН" if self.verbose_mode else "ВЫКЛЮЧЕН"
                        print(f"🔍 Режим отладки: {status}")
                    else:
                        print(f"❌ Неизвестная системная команда: /{command}")
                    continue
                
                # Выбираем режим обработки
                if self.natural_language_mode:
                    # Режим естественного языка
                    if not self.ollama.check_ollama_availability():
                        print("❌ Ollama недоступен для естественного языка!")
                        print("Переключитесь в командный режим: /cmd")
                        continue
                    await self.handle_natural_language_question(command_line)
                else:
                    # Командный режим
                    command, args = self.parse_command(command_line)
                    
                    if command == 'help':
                        self.show_help()
                    elif command == 'status':
                        self.handle_status_command()
                    elif command == 'clear':
                        self.handle_clear_command()
                    elif command == 'tools':
                        await self.handle_tools_command(args)
                    elif command == 'resources':
                        await self.handle_resources_command(args)
                    elif command == 'prompts':
                        await self.handle_prompts_command(args)
                    elif command == 'call':
                        await self.handle_call_command(args)
                    elif command == 'read':
                        await self.handle_read_command(args)
                    elif command == 'prompt':
                        await self.handle_prompt_command(args)
                    else:
                        print(f"❌ Неизвестная команда: {command}")
                        print("💡 Введите 'help' для списка команд или '/nlp' для естественного языка")
                    
            except KeyboardInterrupt:
                print("\n👋 Выход по Ctrl+C")
                break
            except EOFError:
                print("\n👋 Выход по EOF")
                break
            except Exception as e:
                print(f"❌ Неожиданная ошибка: {e}")
    
    async def run(self):
        """Run the interactive chat"""
        self.show_welcome()
        
        if not await self.connect_to_server():
            print("❌ Не удалось подключиться к серверу. Завершение работы.")
            return
        
        # Проверяем Ollama для естественного языка
        if self.ollama.check_ollama_availability():
            print("✅ Ollama доступен! Можете использовать режим естественного языка (/nlp)")
            self.natural_language_mode = True
        else:
            print("⚠️ Ollama недоступен. Работаем в командном режиме (/cmd)")
            print("💡 Для естественного языка запустите: ollama serve")
            self.natural_language_mode = False
        
        try:
            await self.run_interactive_loop()
        finally:
            await self.disconnect_from_server()


async def main():
    """Main function"""
    chat = InteractiveMCPChat()
    await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа прервана пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1) 