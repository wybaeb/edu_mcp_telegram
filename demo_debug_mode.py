#!/usr/bin/env python3
"""
Демонстрация нового режима отладки MCP инструментов
Показывает как AI модель принимает решения о вызове инструментов
"""

import asyncio
import json
from interactive_chat import InteractiveMCPChat


async def demo_debug_mode():
    """Демонстрация режима отладки"""
    print("🔍 === ДЕМОНСТРАЦИЯ РЕЖИМА ОТЛАДКИ MCP ===")
    print("Показываем как AI модель принимает решения о вызове инструментов")
    print()
    
    chat = InteractiveMCPChat()
    
    try:
        # Запуск MCP сервера
        await chat.mcp_client.start_server()
        await chat.mcp_client.initialize()
        
        # Получаем доступные инструменты
        tools = await chat.mcp_client.list_tools()
        print(f"✅ MCP сервер запущен с {len(tools)} инструментами")
        print()
        
        # Демонстрируем режим отладки
        print("🎯 РЕЖИМ ОТЛАДКИ ВКЛЮЧЕН")
        print("Теперь мы видим весь процесс принятия решений AI:")
        print()
        
        # Демонстрируем системный промпт
        print("📋 СИСТЕМНЫЙ ПРОМПТ ДЛЯ МОДЕЛИ:")
        system_prompt = chat.build_system_prompt_with_tools([
            {"name": tool["name"], "description": tool["description"], "parameters": tool["inputSchema"]}
            for tool in tools
        ])
        print(system_prompt[:300] + "...")
        print()
        
        # Демонстрируем парсинг ответа с вызовами инструментов
        print("🤖 ПРИМЕР ОТВЕТА МОДЕЛИ С ВЫЗОВАМИ ИНСТРУМЕНТОВ:")
        mock_response = """Для ответа на ваш вопрос мне нужно получить данные календаря.

[TOOL_CALL:get_available_slots:{}]

На основе полученных данных могу сказать, что у вас есть свободные слоты."""
        
        print(f"Ответ модели: {mock_response}")
        print()
        
        print("🔧 АНАЛИЗ ОТВЕТА:")
        import re
        tool_pattern = r'\[TOOL_CALL:([^:]+):([^\]]+)\]'
        tool_calls = re.findall(tool_pattern, mock_response)
        
        if tool_calls:
            print(f"Найдено {len(tool_calls)} вызовов инструментов:")
            for tool_name, params in tool_calls:
                print(f"  • {tool_name} с параметрами: {params}")
        
        print()
        print("✨ ПРЕИМУЩЕСТВА РЕЖИМА ОТЛАДКИ:")
        print("1. 🎓 Образовательная ценность - студенты видят как работает MCP")
        print("2. 🔍 Прозрачность - понятно какие данные использует AI")
        print("3. 🐛 Отладка - легко найти проблемы в логике")
        print("4. 📊 Оптимизация - можно улучшить эффективность вызовов")
        print()
        
        print("💡 РЕЖИМ МОЖНО ПЕРЕКЛЮЧАТЬ КОМАНДОЙ /debug В ЧАТЕ")
        
    except Exception as e:
        print(f"❌ Ошибка демонстрации: {e}")
    finally:
        await chat.mcp_client.stop_server()


if __name__ == "__main__":
    asyncio.run(demo_debug_mode()) 