#!/usr/bin/env python3
"""
Тестовый клиент для демонстрации работы Educational MCP Server
Использует Ollama для демонстрации интеграции с LLM
"""

import json
import subprocess
import sys
import asyncio
import requests
from typing import Dict, Any, List


class MCPTestClient:
    """Простой тестовый клиент для MCP сервера"""
    
    def __init__(self, server_command: List[str]):
        self.server_process = None
        self.server_command = server_command
        self.request_id = 0
        
    async def start_server(self):
        """Запуск MCP сервера"""
        self.server_process = await asyncio.create_subprocess_exec(
            *self.server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        print("✅ MCP Server запущен")
        
    async def stop_server(self):
        """Остановка MCP сервера"""
        if self.server_process:
            self.server_process.terminate()
            await self.server_process.wait()
            print("🛑 MCP Server остановлен")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Отправка JSON-RPC запроса к серверу"""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        request_data = json.dumps(request) + "\n"
        self.server_process.stdin.write(request_data.encode())
        await self.server_process.stdin.drain()
        
        response_data = await self.server_process.stdout.readline()
        return json.loads(response_data.decode())
    
    async def initialize(self):
        """Инициализация соединения с сервером"""
        response = await self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "educational-test-client",
                "version": "1.0.0"
            }
        })
        
        # Проверяем наличие ошибки (не None)
        if "error" in response and response["error"] is not None:
            raise Exception(f"Ошибка инициализации: {response['error']}")
        
        if "result" not in response:
            raise Exception(f"Нет результата в ответе: {response}")
            
        print("✅ Соединение с MCP сервером установлено")
        return response["result"]
    
    async def list_tools(self):
        """Получить список инструментов"""
        response = await self.send_request("tools/list")
        return response["result"]["tools"]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any] = None):
        """Вызвать инструмент"""
        response = await self.send_request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })
        return response["result"]


class OllamaIntegration:
    """Интеграция с Ollama для демонстрации LLM возможностей"""
    
    def __init__(self, model: str = "mistral:latest", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    def check_ollama_availability(self) -> bool:
        """Проверка доступности Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def query_ollama(self, prompt: str, context: str = "") -> str:
        """Запрос к Ollama"""
        try:
            full_prompt = f"{context}\n\nПользователь: {prompt}\nОтвет:" if context else prompt
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                return f"Ошибка Ollama: {response.status_code}"
                
        except Exception as e:
            return f"Ошибка подключения к Ollama: {str(e)}"


async def demonstrate_mcp_functionality():
    """Демонстрация функциональности MCP сервера"""
    print("🎓 === ДЕМОНСТРАЦИЯ EDUCATIONAL MCP SERVER ===")
    print()
    
    # Запуск MCP сервера
    client = MCPTestClient(["python3", "mcp_server.py"])
    
    try:
        await client.start_server()
        await client.initialize()
        
        print("📋 1. СПИСОК ДОСТУПНЫХ ИНСТРУМЕНТОВ:")
        print("=" * 50)
        
        tools = await client.list_tools()
        for i, tool in enumerate(tools, 1):
            print(f"{i}. {tool['name']}")
            print(f"   📝 {tool['description']}")
            print()
        
        print("🕐 2. ПРОВЕРКА ДОСТУПНЫХ СЛОТОВ:")
        print("=" * 50)
        
        slots_result = await client.call_tool("get_available_slots")
        slots_data = json.loads(slots_result["content"][0]["text"])
        print("Доступные временные слоты:")
        for slot in slots_data["available_slots"]:
            print(f"📅 {slot['date']} ({slot['day_of_week']}): {', '.join(slot['available_times'])}")
        print()
        
        print("📝 3. ПЛАНИРОВАНИЕ ВСТРЕЧИ:")
        print("=" * 50)
        
        meeting_result = await client.call_tool("schedule_meeting", {
            "date": "2024-01-17",
            "time": "10:00", 
            "title": "Демо встреча с клиентом",
            "duration": 60
        })
        meeting_data = json.loads(meeting_result["content"][0]["text"])
        if meeting_data["success"]:
            print(f"✅ {meeting_data['message']}")
            print(f"🆔 ID встречи: {meeting_data['meeting_id']}")
        else:
            print(f"❌ {meeting_data['message']}")
        print()
        
        print("🚀 4. ПЛАН РАЗВИТИЯ:")
        print("=" * 50)
        
        plan_result = await client.call_tool("get_development_plan")
        plan_data = json.loads(plan_result["content"][0]["text"])
        print(f"Текущий уровень: {plan_data['current_level']}")
        print(f"Целевой уровень: {plan_data['target_level']}")
        print("\nНавыки для развития:")
        for skill in plan_data["skills_to_develop"]:
            print(f"• {skill['skill']} ({skill['current_level']} → {skill['target_level']})")
            print(f"  Дедлайн: {skill['deadline']}")
        print()
        
        print("📋 5. ПОИСК ПО РЕГЛАМЕНТАМ:")
        print("=" * 50)
        
        regulations_result = await client.call_tool("search_regulations", {
            "query": "отпуск"
        })
        regulations_data = json.loads(regulations_result["content"][0]["text"])
        print(f"Найдено результатов: {regulations_data['found_count']}")
        for result in regulations_data["results"]:
            print(f"❓ {result['question']}")
            print(f"💡 {result['answer']}")
            print()
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        
    finally:
        await client.stop_server()


async def demonstrate_ollama_integration():
    """Демонстрация интеграции с Ollama"""
    print("\n🤖 === ДЕМОНСТРАЦИЯ ИНТЕГРАЦИИ С OLLAMA ===")
    print()
    
    ollama = OllamaIntegration()
    
    if not ollama.check_ollama_availability():
        print("❌ Ollama недоступен. Убедитесь что:")
        print("   1. Ollama установлен и запущен")
        print("   2. Модель mistral:latest загружена")
        print("   3. Сервис доступен на http://localhost:11434")
        print("\nКоманды для установки:")
        print("   curl -fsSL https://ollama.ai/install.sh | sh")
        print("   ollama pull mistral:latest")
        print("   ollama serve")
        return
    
    print("✅ Ollama доступен!")
    
    # Пример интеграции MCP данных с LLM
    client = MCPTestClient(["python3", "mcp_server.py"])
    
    try:
        await client.start_server()
        await client.initialize()
        
        # Получаем план развития из MCP
        plan_result = await client.call_tool("get_development_plan")
        plan_data = json.loads(plan_result["content"][0]["text"])
        
        # Формируем контекст для LLM
        context = f"""
Ты карьерный консультант. У тебя есть следующая информация о сотруднике:
- Текущий уровень: {plan_data['current_level']}
- Целевой уровень: {plan_data['target_level']}
- Навыки для развития: {', '.join([skill['skill'] for skill in plan_data['skills_to_develop']])}

Отвечай кратко и по делу на русском языке.
"""
        
        print("🧠 Запрос к LLM с контекстом из MCP:")
        query = "Какой навык мне стоит развивать в первую очередь?"
        print(f"❓ Вопрос: {query}")
        
        response = ollama.query_ollama(query, context)
        print(f"🤖 Ответ Ollama: {response}")
        
    except Exception as e:
        print(f"❌ Ошибка интеграции: {e}")
        
    finally:
        await client.stop_server()


def create_demo_script():
    """Создание скрипта для быстрого запуска демо"""
    demo_script = """#!/bin/bash
echo "🎓 Educational MCP Server Demo"
echo "=============================="
echo

echo "Проверка зависимостей..."
python3 -c "import asyncio, json, requests; print('✅ Все зависимости установлены')" || {
    echo "❌ Устанавливаю зависимости..."
    source venv/bin/activate
    pip install -r requirements.txt
}

echo
echo "Запуск демонстрации..."
source venv/bin/activate
python3 test_client.py
"""
    
    with open("demo.sh", "w") as f:
        f.write(demo_script)
    
    # Делаем скрипт исполняемым
    import os
    os.chmod("demo.sh", 0o755)
    
    print("✅ Создан скрипт demo.sh для быстрого запуска")


async def main():
    """Главная функция демонстрации"""
    print("🎯 Educational MCP Server - Test Client")
    print("Демонстрационный клиент для обучения студентов")
    print()
    
    # Основная демонстрация MCP
    await demonstrate_mcp_functionality()
    
    # Демонстрация интеграции с Ollama
    await demonstrate_ollama_integration()
    
    print("\n✨ === ЗАКЛЮЧЕНИЕ ===")
    print("Демонстрация завершена! Вы увидели:")
    print("✅ Как работает MCP протокол")
    print("✅ Список инструментов и их использование")
    print("✅ Работу с календарем и встречами")
    print("✅ Планы развития карьеры")
    print("✅ Поиск по корпоративным регламентам")
    print("✅ Интеграцию с LLM (Ollama)")
    print()
    print("📚 Для студентов: изучите код в файлах:")
    print("   - mcp_server.py (основной сервер)")
    print("   - mcp_types.py (типы данных)")
    print("   - mock_data.py (тестовые данные)")
    print("   - test_client.py (этот файл)")


if __name__ == "__main__":
    create_demo_script()
    asyncio.run(main()) 