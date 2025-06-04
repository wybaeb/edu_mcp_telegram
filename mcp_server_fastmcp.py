#!/usr/bin/env python3
"""
Educational MCP Server for Students using FastMCP
Демонстрационный MCP-сервер для обучающих целей с использованием официальной библиотеки FastMCP
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from mock_data import (
    get_available_slots_for_week, book_meeting, get_development_plan, 
    search_corporate_regulations, AVAILABLE_SLOTS
)

# Create the FastMCP server
mcp = FastMCP("Educational MCP Server")

# === TOOLS ===

@mcp.tool()
def list_tools() -> str:
    """Показать список всех доступных инструментов с описанием"""
    tools_info = [
        {
            "name": "list_tools",
            "description": "Показать список всех доступных инструментов с описанием",
            "parameters": []
        },
        {
            "name": "get_available_slots",
            "description": "Получить доступные временные слоты на текущую неделю",
            "parameters": []
        },
        {
            "name": "schedule_meeting",
            "description": "Запланировать встречу на определенную дату и время",
            "parameters": ["date", "time", "title", "duration"]
        },
        {
            "name": "get_development_plan",
            "description": "Получить индивидуальный план развития в компании",
            "parameters": []
        },
        {
            "name": "search_regulations",
            "description": "Найти информацию по корпоративным регламентам",
            "parameters": ["query"]
        }
    ]
    
    return json.dumps({
        "available_tools": tools_info,
        "total_count": len(tools_info),
        "description": "Полный список доступных инструментов MCP сервера"
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_available_slots() -> str:
    """Получить доступные временные слоты на текущую неделю"""
    slots = get_available_slots_for_week()
    
    formatted_slots = []
    for date, times in slots.items():
        if times:  # Только дни с доступными слотами
            formatted_slots.append({
                "date": date,
                "available_times": times,
                "day_of_week": datetime.strptime(date, "%Y-%m-%d").strftime("%A")
            })
    
    return json.dumps({
        "available_slots": formatted_slots,
        "note": "Все времена указаны в московском часовом поясе",
        "booking_instruction": "Для записи используйте инструмент 'schedule_meeting'"
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def schedule_meeting(date: str, time: str, title: str, duration: int = 60) -> str:
    """Запланировать встречу на определенную дату и время
    
    Args:
        date: Дата встречи в формате YYYY-MM-DD
        time: Время встречи в формате HH:MM
        title: Название встречи
        duration: Продолжительность в минутах (по умолчанию 60)
    """
    result = book_meeting(date, time, title, duration)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def get_development_plan() -> str:
    """Получить индивидуальный план развития в компании"""
    from mock_data import get_development_plan as get_plan_data
    plan = get_plan_data()
    return json.dumps(plan, ensure_ascii=False, indent=2)


@mcp.tool()
def search_regulations(query: str) -> str:
    """Найти информацию по корпоративным регламентам
    
    Args:
        query: Поисковый запрос по регламентам
    """
    if not query:
        return json.dumps({
            "error": "Ошибка: Необходимо указать поисковый запрос"
        }, ensure_ascii=False, indent=2)
    
    results = search_corporate_regulations(query)
    
    if not results:
        return json.dumps({
            "message": "По вашему запросу ничего не найдено",
            "suggestion": "Попробуйте использовать ключевые слова: отпуск, больничный, дресс-код, удаленка, обучение, оборудование"
        }, ensure_ascii=False, indent=2)
    
    return json.dumps({
        "search_query": query,
        "results": results,
        "found_count": len(results)
    }, ensure_ascii=False, indent=2)


# === RESOURCES ===

@mcp.resource("company://calendar/slots")
def available_time_slots() -> str:
    """Доступные временные слоты для встреч"""
    return json.dumps(get_available_slots_for_week(), ensure_ascii=False, indent=2)


@mcp.resource("company://development/plan")
def development_plan() -> str:
    """Индивидуальный план развития"""
    return json.dumps(get_development_plan(), ensure_ascii=False, indent=2)


@mcp.resource("company://regulations/all")
def corporate_regulations() -> str:
    """Корпоративные регламенты и политики"""
    return json.dumps({"regulations": search_corporate_regulations("")}, ensure_ascii=False, indent=2)


# === PROMPTS ===

@mcp.prompt()
def career_advice(current_role: str, goal: str) -> str:
    """Получить совет по карьерному развитию
    
    Args:
        current_role: Текущая должность
        goal: Карьерная цель
    """
    return f"""Ты карьерный консультант. Помоги сотруднику в должности '{current_role}' достичь цели '{goal}'.

Я работаю {current_role} и хочу {goal}. Какие шаги мне предпринять?

Дай конкретные рекомендации по:
- Техническим навыкам для развития
- Практическим проектам
- Обучающим ресурсам
- Временным рамкам"""


@mcp.prompt()
def meeting_agenda(meeting_type: str, participants: str = "команда") -> str:
    """Создать повестку дня для встречи
    
    Args:
        meeting_type: Тип встречи
        participants: Участники (опционально)
    """
    return f"""Создай детальную повестку дня для встречи типа '{meeting_type}' с участниками: {participants}.

Включи следующие элементы:
- Цель встречи
- Основные вопросы для обсуждения
- Временные рамки для каждой темы
- Ожидаемые результаты
- Action items и ответственные

Формат встречи: {meeting_type}
Участники: {participants}"""


# Make the server executable
if __name__ == "__main__":
    import sys
    import logging
    
    # Configure logging to stderr
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Educational MCP Server started with FastMCP!")
    logger.info("📚 Это демонстрационный сервер для обучения студентов")
    logger.info("🔧 Доступные инструменты:")
    logger.info("   - list_tools: Показать список всех доступных инструментов с описанием")
    logger.info("   - get_available_slots: Получить доступные временные слоты на текущую неделю")
    logger.info("   - schedule_meeting: Запланировать встречу на определенную дату и время")
    logger.info("   - get_development_plan: Получить индивидуальный план развития в компании")
    logger.info("   - search_regulations: Найти информацию по корпоративным регламентам")
    logger.info("")
    
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("👋 Educational MCP Server stopped")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1) 