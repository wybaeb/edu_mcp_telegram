#!/usr/bin/env python3
"""
Быстрый тест нового режима отладки
"""

import asyncio
from interactive_chat import InteractiveMCPChat


async def test_debug_mode():
    """Тест режима отладки"""
    print("🧪 Тестирование режима отладки...")
    
    chat = InteractiveMCPChat()
    print(f"Режим отладки по умолчанию: {'ВКЛЮЧЕН' if chat.verbose_mode else 'ВЫКЛЮЧЕН'}")
    
    # Тест переключения
    original_mode = chat.verbose_mode
    chat.verbose_mode = not chat.verbose_mode
    print(f"После переключения: {'ВКЛЮЧЕН' if chat.verbose_mode else 'ВЫКЛЮЧЕН'}")
    
    # Возвращаем обратно
    chat.verbose_mode = original_mode
    print(f"Восстановлено: {'ВКЛЮЧЕН' if chat.verbose_mode else 'ВЫКЛЮЧЕН'}")
    
    print("✅ Тест пройден!")


if __name__ == "__main__":
    asyncio.run(test_debug_mode()) 