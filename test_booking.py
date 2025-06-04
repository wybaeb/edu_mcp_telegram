#!/usr/bin/env python3
"""
Тест логики бронирования встреч
"""

from mock_data import book_meeting, AVAILABLE_SLOTS, check_time_slot_availability

def test_booking_logic():
    """Тестирует логику бронирования встреч"""
    
    print("📅 ДОСТУПНЫЕ СЛОТЫ НА 15 ЯНВАРЯ:")
    print(f"   {AVAILABLE_SLOTS['2024-01-15']}")
    print()
    
    # Тест недоступного слота
    print("❌ ТЕСТ НЕДОСТУПНОГО СЛОТА (13:00):")
    available = check_time_slot_availability('2024-01-15', '13:00', 60)
    print(f"   Слот доступен: {available}")
    
    result = book_meeting('2024-01-15', '13:00', 'Тестовая встреча')
    print(f"   Результат бронирования:")
    print(f"   {result}")
    print()
    
    # Тест доступного слота
    print("✅ ТЕСТ ДОСТУПНОГО СЛОТА (10:00):")
    available = check_time_slot_availability('2024-01-15', '10:00', 60)
    print(f"   Слот доступен: {available}")
    
    result = book_meeting('2024-01-15', '10:00', 'Тестовая встреча')
    print(f"   Результат бронирования:")
    print(f"   {result}")
    print()
    
    # Тест слота в конце диапазона
    print("✅ ТЕСТ ГРАНИЧНОГО СЛОТА (11:00 - в диапазоне 10:00-12:00):")
    available = check_time_slot_availability('2024-01-15', '11:00', 60)
    print(f"   Слот доступен: {available}")
    
    result = book_meeting('2024-01-15', '11:00', 'Тестовая встреча')
    print(f"   Результат бронирования:")
    print(f"   {result}")

if __name__ == "__main__":
    test_booking_logic() 