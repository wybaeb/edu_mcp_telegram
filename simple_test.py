#!/usr/bin/env python3
"""
Простой тест MCP сервера без сложной логики
Демонстрирует прямое взаимодействие через JSON-RPC
"""

import json
import subprocess
import sys

def test_mcp_server():
    """Простой тест MCP сервера"""
    print("🔧 Простой тест MCP сервера")
    print("=" * 40)
    
    # Запуск сервера
    process = subprocess.Popen(
        ["python3", "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # 1. Инициализация
        print("1️⃣ Инициализация...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "simple-test", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        response = json.loads(process.stdout.readline())
        print(f"✅ Инициализация: {response['result']['serverInfo']['name']}")
        
        # 2. Список инструментов
        print("\n2️⃣ Список инструментов...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        response = json.loads(process.stdout.readline())
        tools = response['result']['tools']
        print(f"✅ Найдено инструментов: {len(tools)}")
        for tool in tools:
            print(f"   🔨 {tool['name']}: {tool['description']}")
        
        # 3. Вызов инструмента
        print("\n3️⃣ Вызов инструмента 'get_available_slots'...")
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_available_slots",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(call_request) + "\n")
        process.stdin.flush()
        
        response = json.loads(process.stdout.readline())
        result = json.loads(response['result']['content'][0]['text'])
        print(f"✅ Доступно слотов: {len(result['available_slots'])}")
        
        # 4. Планирование встречи
        print("\n4️⃣ Планирование встречи...")
        meeting_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "schedule_meeting",
                "arguments": {
                    "date": "2024-01-19",
                    "time": "11:00",
                    "title": "Тестовая встреча",
                    "duration": 30
                }
            }
        }
        
        process.stdin.write(json.dumps(meeting_request) + "\n")
        process.stdin.flush()
        
        response = json.loads(process.stdout.readline())
        result = json.loads(response['result']['content'][0]['text'])
        if result['success']:
            print(f"✅ Встреча запланирована: {result['meeting_id']}")
        else:
            print(f"❌ Ошибка: {result['message']}")
        
        print("\n🎉 Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_mcp_server() 