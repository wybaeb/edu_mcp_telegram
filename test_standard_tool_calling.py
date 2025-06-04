#!/usr/bin/env python3
"""
Тест стандартного tool calling в Ollama
"""

import asyncio
import json
from interactive_chat import InteractiveMCPChat, OllamaIntegration
from test_client import MCPTestClient


async def test_standard_tool_calling():
    """Тест стандартного подхода к tool calling"""
    print("🧪 === ТЕСТ СТАНДАРТНОГО TOOL CALLING ===")
    print()
    
    # Инициализация
    mcp_client = MCPTestClient(["python3", "mcp_server.py"])
    ollama = OllamaIntegration()
    
    # Проверяем Ollama
    if not ollama.check_ollama_availability():
        print("❌ Ollama недоступен! Запустите: ollama serve")
        return
    
    print("✅ Ollama доступен")
    
    try:
        # Запускаем MCP сервер
        await mcp_client.start_server()
        await mcp_client.initialize()
        print("✅ MCP сервер запущен")
        
        # Получаем MCP инструменты
        mcp_tools = await mcp_client.list_tools()
        print(f"✅ Получено {len(mcp_tools)} MCP инструментов")
        
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
        
        print(f"✅ Преобразовано в формат Ollama")
        print()
        
        # Тестовые сценарии
        test_cases = [
            "Покажи мне доступные временные слоты",
            "Запланируй встречу на понедельник в 13:00 по теме 'Обсуждение проекта'",
            "Найди регламент про отпуск"
        ]
        
        for i, question in enumerate(test_cases, 1):
            print(f"📝 ТЕСТ {i}: {question}")
            print("-" * 50)
            
            # Подготавливаем сообщения
            messages = [
                {
                    "role": "system",
                    "content": """Ты корпоративный помощник. Используй доступные инструменты для ответа на вопросы пользователя. Отвечай на русском языке."""
                },
                {
                    "role": "user", 
                    "content": question
                }
            ]
            
            print("🤖 Отправляю первый запрос...")
            
            # Первый запрос в Ollama
            response = ollama.chat_with_tools(messages, ollama_tools)
            
            if "error" in response:
                print(f"❌ Ошибка: {response['error']}")
                continue
                
            assistant_message = response["message"]
            print(f"📤 Ответ модели получен")
            
            # Проверяем tool calls
            if assistant_message.get("tool_calls"):
                tool_calls = assistant_message["tool_calls"]
                print(f"🔧 Модель вызвала {len(tool_calls)} инструментов:")
                
                # Добавляем ответ ассистента
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.get("content", ""),
                    "tool_calls": tool_calls
                })
                
                # Выполняем tool calls
                for tool_call in tool_calls:
                    function = tool_call["function"]
                    tool_name = function["name"]
                    tool_args = function["arguments"]
                    
                    print(f"   📞 {tool_name}({tool_args})")
                    
                    try:
                        # Вызываем MCP инструмент
                        result = await mcp_client.call_tool(tool_name, tool_args)
                        tool_result = result["content"][0]["text"]
                        
                        print(f"   ✅ Результат: {tool_result[:100]}...")
                        
                        # Добавляем результат
                        messages.append({
                            "role": "tool",
                            "content": tool_result
                        })
                        
                    except Exception as e:
                        error_msg = f"Ошибка выполнения {tool_name}: {e}"
                        print(f"   ❌ {error_msg}")
                        
                        messages.append({
                            "role": "tool",
                            "content": error_msg
                        })
                
                # Второй запрос с результатами
                print("🔄 Отправляю результаты обратно в модель...")
                
                final_response = ollama.chat_with_tools(messages, ollama_tools)
                
                if "error" in final_response:
                    print(f"❌ Ошибка финального запроса: {final_response['error']}")
                else:
                    final_content = final_response["message"].get("content", "")
                    print(f"💬 ФИНАЛЬНЫЙ ОТВЕТ: {final_content}")
                    
            else:
                # Модель не вызвала инструменты
                content = assistant_message.get("content", "")
                print(f"ℹ️ Модель не вызвала инструменты")
                print(f"💬 ОТВЕТ: {content}")
            
            print()
            print("=" * 60)
            print()
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await mcp_client.stop_server()


if __name__ == "__main__":
    asyncio.run(test_standard_tool_calling()) 