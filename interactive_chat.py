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
        print("  /exit или /quit - выход")
        print()
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
            
        else:
            print(f"❌ Неизвестная команда: {cmd}")
            print("💡 Введите /help для справки")
            print()
    
    async def handle_question(self, question: str):
        """Обработка обычного вопроса через LLM с контекстом MCP"""
        print("🤔 Обрабатываю ваш вопрос...")
        
        # Добавляем вопрос в историю
        self.conversation_history.append({
            "role": "user",
            "content": question
        })
        
        try:
            # Определяем нужные ли нам данные из MCP
            context_data = await self.gather_context_for_question(question)
            
            # Формируем контекст для LLM
            system_context = self.build_system_context(context_data)
            
            # Формируем полный промпт
            conversation_context = self.build_conversation_context()
            full_prompt = f"{system_context}\n\n{conversation_context}\n\nПользователь: {question}\n\nПомощник:"
            
            # Отправляем в Ollama
            response = self.ollama.query_ollama(full_prompt)
            
            # Выводим ответ
            print(f"🤖 Помощник: {response}")
            print()
            
            # Добавляем ответ в историю
            self.conversation_history.append({
                "role": "assistant", 
                "content": response
            })
            
        except Exception as e:
            print(f"❌ Ошибка обработки вопроса: {e}")
            print()
    
    async def gather_context_for_question(self, question: str) -> Dict[str, Any]:
        """Собираем контекстную информацию из MCP для вопроса"""
        context = {}
        question_lower = question.lower()
        
        try:
            # Если вопрос про время, слоты, встречи
            if any(word in question_lower for word in ['время', 'слот', 'встреча', 'календарь', 'свободн']):
                result = await self.mcp_client.call_tool("get_available_slots")
                context['calendar'] = json.loads(result["content"][0]["text"])
            
            # Если вопрос про развитие, карьеру, навыки
            if any(word in question_lower for word in ['развитие', 'карьер', 'навык', 'план', 'обучен']):
                result = await self.mcp_client.call_tool("get_development_plan")
                context['development'] = json.loads(result["content"][0]["text"])
            
            # Если вопрос про правила, регламенты, политики
            if any(word in question_lower for word in ['правил', 'регламент', 'политик', 'отпуск', 'больничн', 'дресс']):
                # Пытаемся найти релевантные регламенты
                for keyword in ['отпуск', 'больничный', 'дресс-код', 'удаленная работа', 'обучение']:
                    if keyword in question_lower:
                        result = await self.mcp_client.call_tool("search_regulations", {"query": keyword})
                        regulations_data = json.loads(result["content"][0]["text"])
                        if regulations_data.get('results'):
                            context['regulations'] = regulations_data
                            break
        
        except Exception as e:
            print(f"⚠️  Ошибка сбора контекста: {e}")
        
        return context
    
    def build_system_context(self, context_data: Dict[str, Any]) -> str:
        """Строим системный контекст для LLM"""
        context_parts = [
            "Ты полезный корпоративный помощник. У тебя есть доступ к следующим данным компании:"
        ]
        
        if 'calendar' in context_data:
            calendar_info = "КАЛЕНДАРЬ:\n"
            for slot in context_data['calendar'].get('available_slots', []):
                calendar_info += f"- {slot['date']}: {', '.join(slot['available_times'])}\n"
            context_parts.append(calendar_info)
        
        if 'development' in context_data:
            dev_info = f"ПЛАН РАЗВИТИЯ:\n"
            dev_data = context_data['development']
            dev_info += f"- Текущий уровень: {dev_data['current_level']}\n"
            dev_info += f"- Целевой уровень: {dev_data['target_level']}\n"
            dev_info += "- Навыки для развития:\n"
            for skill in dev_data['skills_to_develop']:
                dev_info += f"  • {skill['skill']} ({skill['current_level']} → {skill['target_level']}, дедлайн: {skill['deadline']})\n"
            context_parts.append(dev_info)
        
        if 'regulations' in context_data:
            reg_info = "КОРПОРАТИВНЫЕ РЕГЛАМЕНТЫ:\n"
            for result in context_data['regulations'].get('results', []):
                reg_info += f"- {result['question']}\n  {result['answer']}\n\n"
            context_parts.append(reg_info)
        
        context_parts.append("Отвечай на русском языке, кратко и по делу. Используй предоставленную информацию.")
        
        return "\n\n".join(context_parts)
    
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