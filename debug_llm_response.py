#!/usr/bin/env python3
"""
Отладка ответов модели Ollama
"""

import asyncio
from interactive_chat import InteractiveMCPChat


async def debug_llm_response():
    """Отладка ответов модели"""
    print("🔍 === ОТЛАДКА ОТВЕТОВ МОДЕЛИ ===")
    print()
    
    chat = InteractiveMCPChat()
    
    try:
        # Запуск MCP сервера
        await chat.mcp_client.start_server()
        await chat.mcp_client.initialize()
        
        # Получаем инструменты
        tools = await chat.mcp_client.list_tools()
        tools_for_llm = [{"name": tool["name"], "description": tool["description"], "parameters": tool["inputSchema"]} for tool in tools]
        
        print("✅ MCP сервер запущен")
        print()
        
        # Проверяем Ollama
        if not chat.ollama.check_ollama_availability():
            print("❌ Ollama недоступен - тестируем только парсинг")
            
            # Тестируем парсинг с mock ответом
            mock_response = """Для планирования встречи воспользуюсь инструментом:

[TOOL_CALL:schedule_meeting:{"date":"2024-01-15","time":"13:00","title":"Тестовая встреча"}]

Встреча запланирована."""
            
            print(f"📝 MOCK ОТВЕТ МОДЕЛИ:")
            print(f"   {mock_response}")
            print()
            
            import re
            tool_pattern = r'\[TOOL_CALL:([^:]+):([^\]]+)\]'
            tool_calls = re.findall(tool_pattern, mock_response)
            
            print(f"🔧 НАЙДЕННЫЕ ВЫЗОВЫ ИНСТРУМЕНТОВ: {len(tool_calls)}")
            for i, (tool_name, params) in enumerate(tool_calls, 1):
                print(f"   {i}. {tool_name} с параметрами: {params}")
            
            if tool_calls:
                print()
                print("🔄 ТЕСТИРУЕМ ОБРАБОТКУ:")
                final_response = await chat.process_llm_response(mock_response)
                print(f"📋 ФИНАЛЬНЫЙ ОТВЕТ:")
                print(f"   {final_response}")
        else:
            # Тестируем с реальной моделью
            print("✅ Ollama доступен - тестируем реальный запрос")
            
            system_prompt = chat.build_system_prompt_with_tools(tools_for_llm)
            question = "Запланируй встречу на понедельник на 13:00"
            full_prompt = f"{system_prompt}\n\nПользователь: {question}\n\nПомощник:"
            
            print("🤖 ОТПРАВЛЯЕМ ЗАПРОС В OLLAMA...")
            print("📋 СИСТЕМНЫЙ ПРОМПТ (первые 200 символов):")
            print(f"   {system_prompt[:200]}...")
            print()
            
            response = chat.ollama.query_ollama(full_prompt)
            
            print(f"📤 ОТВЕТ МОДЕЛИ:")
            print(f"   {response}")
            print()
            
            # Проверяем парсинг
            import re
            tool_pattern = r'\[TOOL_CALL:([^:]+):([^\]]+)\]'
            tool_calls = re.findall(tool_pattern, response)
            
            print(f"🔧 НАЙДЕННЫЕ ВЫЗОВЫ ИНСТРУМЕНТОВ: {len(tool_calls)}")
            if tool_calls:
                for i, (tool_name, params) in enumerate(tool_calls, 1):
                    print(f"   {i}. {tool_name} с параметрами: {params}")
            else:
                print("   ❌ НЕ НАЙДЕНО вызовов инструментов в формате [TOOL_CALL:name:params]")
                print("   💡 Возможно, модель не следует заданному формату")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await chat.mcp_client.stop_server()


if __name__ == "__main__":
    asyncio.run(debug_llm_response()) 