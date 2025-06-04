#!/usr/bin/env python3
"""
Быстрый тест tool calling с llama3.2:3b-instruct
"""

import asyncio
import json
from interactive_chat import OllamaIntegration
from test_client import MCPTestClient


async def test_llama_tool_calling():
    """Тест llama3.2 с tool calling"""
    print("🧪 === ТЕСТ LLAMA3.2 TOOL CALLING ===")
    print()
    
    # Инициализация
    mcp_client = MCPTestClient(["python3", "mcp_server.py"])
    ollama = OllamaIntegration()  # Теперь использует llama3.2:3b-instruct-q5_K_M
    
    print(f"🤖 Модель: {ollama.model}")
    
    # Проверяем Ollama
    if not ollama.check_ollama_availability():
        print("❌ Ollama недоступен!")
        return
    
    print("✅ Ollama доступен")
    
    try:
        # Запускаем MCP сервер
        await mcp_client.start_server()
        await mcp_client.initialize()
        
        # Получаем MCP инструменты
        mcp_tools = await mcp_client.list_tools()
        
        # Преобразуем в формат Ollama
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
        
        print(f"✅ Загружено {len(ollama_tools)} инструментов")
        print()
        
        # Простой тест
        question = "Покажи доступные временные слоты"
        print(f"📝 ТЕСТ: {question}")
        print("-" * 50)
        
        # Подготавливаем сообщения
        messages = [
            {
                "role": "system",
                "content": """You are a helpful assistant. You have access to tools. When user asks for time slots, use get_available_slots tool. Always use tools when needed."""
            },
            {
                "role": "user", 
                "content": question
            }
        ]
        
        print("🤖 Отправляю запрос...")
        
        # Запрос в Ollama
        response = ollama.chat_with_tools(messages, ollama_tools)
        
        if "error" in response:
            print(f"❌ Ошибка: {response['error']}")
            return
            
        assistant_message = response["message"]
        print(f"📤 Ответ получен")
        
        # Проверяем tool calls
        if assistant_message.get("tool_calls"):
            tool_calls = assistant_message["tool_calls"]
            print(f"🎉 УСПЕХ! Модель вызвала {len(tool_calls)} инструментов:")
            
            for tool_call in tool_calls:
                function = tool_call["function"]
                print(f"   📞 {function['name']}({function['arguments']})")
                
        else:
            print("❌ Модель не вызвала инструменты")
            content = assistant_message.get("content", "")
            print(f"💬 Ответ: {content[:200]}...")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await mcp_client.stop_server()


if __name__ == "__main__":
    asyncio.run(test_llama_tool_calling()) 