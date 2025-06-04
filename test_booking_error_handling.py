#!/usr/bin/env python3
"""
Тест правильной обработки ошибок бронирования в интерактивном чате
"""

import asyncio
import json
from interactive_chat import InteractiveMCPChat


async def test_booking_error_handling():
    """Тестирует правильную обработку ошибок при бронировании"""
    print("🧪 === ТЕСТ ОБРАБОТКИ ОШИБОК БРОНИРОВАНИЯ ===")
    print()
    
    chat = InteractiveMCPChat()
    
    try:
        # Запуск MCP сервера
        await chat.mcp_client.start_server()
        await chat.mcp_client.initialize()
        
        print("✅ MCP сервер запущен")
        print()
        
        # Тестируем обработку ошибки бронирования
        print("🔧 ТЕСТ: Попытка забронировать недоступный слот")
        mock_response_with_tool_call = """Для планирования встречи воспользуюсь инструментом:

[TOOL_CALL:schedule_meeting:{"date":"2024-01-15","time":"13:00","title":"Тестовая встреча"}]

Встреча успешно запланирована!"""
        
        print("📝 Имитируем ответ модели с вызовом инструмента:")
        print(f"   {mock_response_with_tool_call}")
        print()
        
        print("🔄 Обрабатываем ответ (включая вызов реального инструмента):")
        processed_response = await chat.process_llm_response(mock_response_with_tool_call)
        
        print("📋 ФИНАЛЬНЫЙ ОТВЕТ:")
        print(f"   {processed_response}")
        print()
        
        # Проверяем что ответ содержит корректную информацию об ошибке
        if '"success": false' in processed_response:
            print("✅ ОТЛИЧНО: Ответ корректно показывает ошибку бронирования")
        else:
            print("❌ ПРОБЛЕМА: Ответ не показывает ошибку бронирования")
        
        if 'available_alternatives' in processed_response:
            print("✅ ОТЛИЧНО: Ответ содержит доступные альтернативы")
        else:
            print("❌ ПРОБЛЕМА: Ответ не содержит доступные альтернативы")
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
    finally:
        await chat.mcp_client.stop_server()


if __name__ == "__main__":
    asyncio.run(test_booking_error_handling()) 