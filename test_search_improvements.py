#!/usr/bin/env python3
"""
Тест улучшенного поиска регламентов
"""

from mock_data import search_corporate_regulations, normalize_text, get_search_keywords


def test_search_improvements():
    """Тестируем улучшенный поиск"""
    print("🔍 === ТЕСТ УЛУЧШЕННОГО ПОИСКА ===")
    print()
    
    # Тестовые запросы
    test_queries = [
        "дресс-код",
        "дресс код", 
        "dress code",
        "одежда",
        "отпуск",
        "vacation",
        "удаленка",
        "remote",
        "больничный",
        "рабочее время",
        "график",
        "обучение",
        "курсы"
    ]
    
    for query in test_queries:
        print(f"📝 Запрос: '{query}'")
        
        # Показываем ключевые слова
        keywords = get_search_keywords(query)
        print(f"   🔑 Ключевые слова: {keywords}")
        
        # Ищем
        results = search_corporate_regulations(query)
        
        if results:
            print(f"   ✅ Найдено {len(results)} результатов:")
            for result in results:
                print(f"      • {result['topic']}: {result['question']}")
        else:
            print(f"   ❌ Ничего не найдено")
        
        print()


if __name__ == "__main__":
    test_search_improvements() 