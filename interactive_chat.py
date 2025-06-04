#!/usr/bin/env python3
"""
Интерактивный чат с моделью через MCP сервер
Позволяет общаться с LLM и использовать MCP инструменты в реальном времени
"""

import json
import asyncio
import sys
import signal
import requests
from typing import Dict, Any, List, Optional
from test_client import MCPTestClient


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
    """Интерактивный чат с MCP сервером и Ollama"""
    
    def __init__(self):
        self.mcp_client = MCPTestClient(["python3", "mcp_server.py"])
        self.ollama = OllamaIntegration()
        self.conversation_history = []
        self.available_tools = []
        self.running = True
        self.verbose_mode = True  # По умолчанию показываем процесс работы
        
    async def start(self):
        """Запуск интерактивного чата"""
        print("🤖 === ИНТЕРАКТИВНЫЙ CHAT С MCP + OLLAMA ===")
        print("Добро пожаловать в демонстрационный чат!")
        print("Вы можете задавать вопросы и использовать корпоративные инструменты.")
        print()
        
        # Проверка Ollama
        if not self.ollama.check_ollama_availability():
            print("❌ Ollama недоступен! Запустите: ollama serve")
            print("И убедитесь что модель llama3.2:3b-instruct-q5_K_M загружена: ollama pull llama3.2:3b-instruct-q5_K_M")
            return
        
        print("✅ Ollama подключен!")
        
        # Запуск MCP сервера
        try:
            await self.mcp_client.start_server()
            await self.mcp_client.initialize()
            self.available_tools = await self.mcp_client.list_tools()
            print(f"✅ MCP сервер запущен с {len(self.available_tools)} инструментами")
            print()
            
            # Показываем доступные команды
            self.show_help()
            
            # Основной цикл чата
            await self.chat_loop()
            
        except Exception as e:
            print(f"❌ Ошибка запуска: {e}")
        finally:
            await self.mcp_client.stop_server()
    
    def show_help(self):
        """Показать справку по доступным командам"""
        print("📋 ДОСТУПНЫЕ КОМАНДЫ:")
        print("  /help - показать эту справку")
        print("  /tools - показать доступные MCP инструменты")
        print("  /slots - показать доступные временные слоты")
        print("  /plan - показать план развития")
        print("  /meet <дата> <время> <название> - запланировать встречу")
        print("  /search <запрос> - поиск по регламентам")
        print("  /history - показать историю разговора")
        print("  /clear - очистить историю")
        print("  /debug - переключить режим отладки (показ MCP инструментов)")
        print("  /exit или /quit - выход")
        print()
        debug_status = "ВКЛЮЧЕН" if self.verbose_mode else "ВЫКЛЮЧЕН"
        print(f"🔍 Режим отладки: {debug_status}")
        print("💬 Или просто задайте любой вопрос - я отвечу используя доступные данные!")
        print("=" * 60)
        print()
    
    async def chat_loop(self):
        """Основной цикл интерактивного чата"""
        while self.running:
            try:
                # Получаем ввод пользователя
                user_input = input("👤 Вы: ").strip()
                
                if not user_input:
                    continue
                    
                # Обработка команд
                if user_input.startswith('/'):
                    await self.handle_command(user_input)
                else:
                    # Обычный вопрос - отправляем в LLM с контекстом
                    await self.handle_question(user_input)
                    
            except KeyboardInterrupt:
                print("\n👋 До свидания!")
                self.running = False
            except EOFError:
                print("\n👋 До свидания!")
                self.running = False
            except Exception as e:
                print(f"❌ Ошибка: {e}")
    
    async def handle_command(self, command: str):
        """Обработка команд чата"""
        parts = command[1:].split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd in ['exit', 'quit']:
            self.running = False
            print("👋 До свидания!")
            
        elif cmd == 'help':
            self.show_help()
            
        elif cmd == 'tools':
            print("🔧 ДОСТУПНЫЕ MCP ИНСТРУМЕНТЫ:")
            for i, tool in enumerate(self.available_tools, 1):
                print(f"{i}. {tool['name']}")
                print(f"   📝 {tool['description']}")
            print()
            
        elif cmd == 'slots':
            try:
                result = await self.mcp_client.call_tool("get_available_slots")
                data = json.loads(result["content"][0]["text"])
                print("📅 ДОСТУПНЫЕ ВРЕМЕННЫЕ СЛОТЫ:")
                for slot in data["available_slots"]:
                    print(f"   {slot['date']}: {', '.join(slot['available_times'])}")
                print()
            except Exception as e:
                print(f"❌ Ошибка получения слотов: {e}")
                
        elif cmd == 'plan':
            try:
                result = await self.mcp_client.call_tool("get_development_plan")
                data = json.loads(result["content"][0]["text"])
                print("🚀 ПЛАН РАЗВИТИЯ:")
                print(f"   Текущий: {data['current_level']}")
                print(f"   Цель: {data['target_level']}")
                print("   Навыки:")
                for skill in data["skills_to_develop"]:
                    print(f"   • {skill['skill']} ({skill['current_level']} → {skill['target_level']})")
                print()
            except Exception as e:
                print(f"❌ Ошибка получения плана: {e}")
                
        elif cmd == 'meet':
            if len(args) < 3:
                print("❌ Использование: /meet <дата> <время> <название>")
                print("   Пример: /meet 2024-01-19 14:00 Встреча с командой")
            else:
                date = args[0]
                time = args[1]
                title = " ".join(args[2:])
                try:
                    result = await self.mcp_client.call_tool("schedule_meeting", {
                        "date": date,
                        "time": time,
                        "title": title
                    })
                    data = json.loads(result["content"][0]["text"])
                    if data["success"]:
                        print(f"✅ {data['message']}")
                    else:
                        print(f"❌ {data['message']}")
                        if data.get('available_alternatives'):
                            print(f"   Доступные варианты: {', '.join(data['available_alternatives'])}")
                    print()
                except Exception as e:
                    print(f"❌ Ошибка планирования: {e}")
                    
        elif cmd == 'search':
            if not args:
                print("❌ Использование: /search <запрос>")
                print("   Пример: /search отпуск")
            else:
                query = " ".join(args)
                try:
                    result = await self.mcp_client.call_tool("search_regulations", {
                        "query": query
                    })
                    data = json.loads(result["content"][0]["text"])
                    if data.get('results'):
                        print(f"🔍 РЕЗУЛЬТАТЫ ПОИСКА ПО '{query}':")
                        for res in data['results']:
                            print(f"❓ {res['question']}")
                            print(f"💡 {res['answer']}")
                            print()
                    else:
                        print(f"❌ По запросу '{query}' ничего не найдено")
                        print("💡 Попробуйте: отпуск, больничный, дресс-код, удаленка")
                        print()
                except Exception as e:
                    print(f"❌ Ошибка поиска: {e}")
                    
        elif cmd == 'history':
            print("📜 ИСТОРИЯ РАЗГОВОРА:")
            if not self.conversation_history:
                print("   Пока пусто")
            else:
                for i, msg in enumerate(self.conversation_history[-10:], 1):  # Последние 10
                    print(f"{i}. {msg['role']}: {msg['content'][:100]}...")
            print()
            
        elif cmd == 'clear':
            self.conversation_history.clear()
            print("🧹 История очищена")
            print()
            
        elif cmd == 'debug':
            self.verbose_mode = not self.verbose_mode
            status = "ВКЛЮЧЕН" if self.verbose_mode else "ВЫКЛЮЧЕН"
            print(f"🔍 Режим отладки: {status}")
            if self.verbose_mode:
                print("   Теперь вы будете видеть какие MCP инструменты использует AI")
            else:
                print("   Отладочная информация скрыта")
            print()
            
        else:
            print(f"❌ Неизвестная команда: {cmd}")
            print("💡 Введите /help для справки")
            print()
    
    async def handle_question(self, question: str):
        """Обработка обычного вопроса через LLM с контекстом MCP"""
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
            # Получаем список доступных MCP инструментов
            if self.verbose_mode:
                print("🔧 Получаю список доступных MCP инструментов...")
            
            mcp_tools = await self.mcp_client.list_tools()
            
            # Преобразуем MCP инструменты в формат Ollama
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
                result = await self.mcp_client.call_tool(tool_name, tool_args)
                tool_result = result["content"][0]["text"]
                
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


def setup_signal_handler():
    """Настройка обработчика сигналов для корректного завершения"""
    def signal_handler(sig, frame):
        print("\n👋 Получен сигнал завершения. До свидания!")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Главная функция"""
    setup_signal_handler()
    
    chat = InteractiveMCPChat()
    await chat.start()


if __name__ == "__main__":
    asyncio.run(main()) 