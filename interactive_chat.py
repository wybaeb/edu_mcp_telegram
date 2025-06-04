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
from test_client import MCPTestClient, OllamaIntegration


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
            print("И убедитесь что модель mistral:latest загружена: ollama pull mistral:latest")
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
            
            available_tools = await self.mcp_client.list_tools()
            
            # Преобразуем MCP инструменты в формат для Ollama
            tools_for_llm = []
            for tool in available_tools:
                tools_for_llm.append({
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                })
            
            if self.verbose_mode:
                print(f"✅ Доступно {len(tools_for_llm)} MCP инструментов:")
                for tool in tools_for_llm:
                    print(f"   • {tool['name']}: {tool['description']}")
                print()
            
            # Формируем системный промпт с описанием доступных инструментов
            system_prompt = self.build_system_prompt_with_tools(tools_for_llm)
            
            # Формируем контекст разговора
            conversation_context = self.build_conversation_context()
            
            # Полный промпт для модели
            full_prompt = f"{system_prompt}\n\n{conversation_context}\n\nПользователь: {question}\n\nПомощник:"
            
            if self.verbose_mode:
                print("🤖 Отправляю запрос в Ollama с доступными инструментами...")
            
            # Отправляем запрос в Ollama
            response = self.ollama.query_ollama(full_prompt)
            
            # Анализируем ответ модели на предмет вызова инструментов
            final_response = await self.process_llm_response(response)
            
            if self.verbose_mode:
                print("=" * 60)
                
            # Выводим финальный ответ
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
    
    def build_conversation_context(self) -> str:
        """Строим контекст разговора"""
        if not self.conversation_history:
            return ""
        
        # Берем последние 6 сообщений для контекста
        recent_history = self.conversation_history[-6:]
        context_lines = []
        
        for msg in recent_history:
            role = "Пользователь" if msg['role'] == 'user' else "Помощник"
            context_lines.append(f"{role}: {msg['content']}")
        
        return "\nПРЕДЫДУЩИЙ КОНТЕКСТ:\n" + "\n".join(context_lines)

    def build_system_prompt_with_tools(self, tools_for_llm: List[Dict[str, Any]]) -> str:
        """Строим системный промпт с описанием доступных инструментов"""
        system_prompt = """Ты полезный корпоративный помощник. У тебя есть доступ к следующим инструментам:

"""
        for tool in tools_for_llm:
            system_prompt += f"- {tool['name']}: {tool['description']}\n"
        
        system_prompt += """
ВАЖНО: Если для ответа на вопрос нужны данные из инструментов, используй следующий формат:
[TOOL_CALL:имя_инструмента:параметры]

Примеры:
- [TOOL_CALL:get_available_slots:{}]
- [TOOL_CALL:schedule_meeting:{"date":"2024-01-19","time":"14:00","title":"Встреча"}]
- [TOOL_CALL:search_regulations:{"query":"отпуск"}]

После вызова инструмента я предоставлю тебе результат, и ты сможешь дать полный ответ.
Отвечай на русском языке, кратко и по делу."""
        return system_prompt

    async def process_llm_response(self, response: str) -> str:
        """Обрабатываем ответ модели и вызываем необходимые инструменты"""
        import re
        
        # Ищем вызовы инструментов в формате [TOOL_CALL:name:params]
        tool_pattern = r'\[TOOL_CALL:([^:]+):([^\]]+)\]'
        tool_calls = re.findall(tool_pattern, response)
        
        if not tool_calls:
            # Нет вызовов инструментов - возвращаем ответ как есть
            return response
        
        if self.verbose_mode:
            print(f"🔧 Модель запросила {len(tool_calls)} инструментов:")
        
        # Обрабатываем каждый вызов инструмента
        final_response = response
        for tool_name, params_str in tool_calls:
            try:
                if self.verbose_mode:
                    print(f"   📞 Вызываю {tool_name} с параметрами: {params_str}")
                
                # Парсим параметры (могут быть JSON или пустые)
                try:
                    params = json.loads(params_str) if params_str.strip() != '{}' else {}
                except json.JSONDecodeError:
                    params = {}
                
                # Вызываем MCP инструмент
                result = await self.mcp_client.call_tool(tool_name, params)
                tool_result = result["content"][0]["text"]
                
                if self.verbose_mode:
                    print(f"   ✅ Результат {tool_name}: {tool_result[:100]}...")
                
                # Заменяем вызов инструмента на результат
                tool_call_pattern = f"\\[TOOL_CALL:{tool_name}:{re.escape(params_str)}\\]"
                final_response = re.sub(tool_call_pattern, tool_result, final_response)
                
            except Exception as e:
                error_msg = f"Ошибка вызова {tool_name}: {e}"
                if self.verbose_mode:
                    print(f"   ❌ {error_msg}")
                final_response = re.sub(f"\\[TOOL_CALL:{tool_name}:{re.escape(params_str)}\\]", 
                                      error_msg, final_response)
        
        return final_response


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