from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Заглушки для календаря и встреч
MOCK_CALENDAR = {
    "2024-01-15": [
        {"time": "09:00", "duration": 60, "title": "Занято - Планерка команды"},
        {"time": "14:00", "duration": 30, "title": "Занято - 1:1 с менеджером"}
    ],
    "2024-01-16": [
        {"time": "10:00", "duration": 120, "title": "Занято - Разработка"}
    ],
    "2024-01-17": [],
    "2024-01-18": [
        {"time": "15:00", "duration": 60, "title": "Занято - Код-ревью"}
    ],
    "2024-01-19": []
}

# Доступные временные слоты (свободное время)
AVAILABLE_SLOTS = {
    "2024-01-15": ["10:00-12:00", "16:00-18:00"],
    "2024-01-16": ["09:00-10:00", "14:00-17:00"], 
    "2024-01-17": ["09:00-18:00"],
    "2024-01-18": ["09:00-15:00", "16:00-18:00"],
    "2024-01-19": ["09:00-18:00"]
}

# Индивидуальный план развития
DEVELOPMENT_PLAN = {
    "current_level": "Junior Developer",
    "target_level": "Middle Developer",
    "skills_to_develop": [
        {
            "skill": "Python",
            "current_level": "Intermediate",
            "target_level": "Advanced",
            "activities": [
                "Изучить продвинутые возможности Python (декораторы, метаклассы)",
                "Сделать pet-проект с использованием Django/FastAPI",
                "Прочитать 'Effective Python' Бретта Слаткина"
            ],
            "deadline": "2024-03-01"
        },
        {
            "skill": "Архитектура ПО",
            "current_level": "Beginner",
            "target_level": "Intermediate", 
            "activities": [
                "Изучить паттерны проектирования",
                "Прочитать 'Clean Architecture' Роберта Мартина",
                "Поучаствовать в архитектурных решениях команды"
            ],
            "deadline": "2024-04-01"
        },
        {
            "skill": "Тестирование",
            "current_level": "Beginner",
            "target_level": "Intermediate",
            "activities": [
                "Изучить pytest на продвинутом уровне",
                "Написать интеграционные тесты для проектов",
                "Изучить TDD подход"
            ],
            "deadline": "2024-02-15"
        }
    ],
    "soft_skills": [
        {
            "skill": "Коммуникация",
            "activities": [
                "Участвовать в технических презентациях",
                "Проводить код-ревью с комментариями",
                "Помогать младшим разработчикам"
            ]
        }
    ],
    "next_review_date": "2024-02-01"
}

# Корпоративные регламенты
CORPORATE_REGULATIONS = {
    "working_hours": {
        "question": "Какие рабочие часы в компании?",
        "answer": "Рабочие часы: 9:00-18:00 по московскому времени. Возможен гибкий график ±2 часа по согласованию с руководителем. Обеденный перерыв: 13:00-14:00."
    },
    "vacation_policy": {
        "question": "Как оформить отпуск?",
        "answer": "Отпуск оформляется через HR-систему минимум за 2 недели. Ежегодно предоставляется 28 календарных дней отпуска. Для отпуска более 5 дней требуется согласование с руководителем."
    },
    "remote_work": {
        "question": "Политика удаленной работы?",
        "answer": "Удаленная работа возможна до 3 дней в неделю по согласованию с руководителем. Полностью удаленная работа рассматривается индивидуально. Обязательное присутствие в офисе по вторникам и четвергам."
    },
    "dress_code": {
        "question": "Есть ли дресс-код?",
        "answer": "Дресс-код: business casual. При встречах с клиентами - деловой стиль. В пятницу можно casual. Запрещены: шорты, открытая обувь, майки с принтами."
    },
    "sick_leave": {
        "question": "Как оформить больничный?",
        "answer": "При болезни уведомить руководителя до 10:00. Больничный лист предоставить в течение 3 дней. Короткие больничные (1-2 дня) можно взять без справки, но не более 5 дней в году."
    },
    "equipment_policy": {
        "question": "Политика использования рабочего оборудования?",
        "answer": "Рабочий ноутбук можно брать домой для удаленной работы. Запрещено устанавливать нелицензионное ПО. Личное использование интернета ограничено разумными пределами. Все изменения в конфигурации согласовываются с IT."
    },
    "learning_budget": {
        "question": "Есть ли бюджет на обучение?",
        "answer": "Ежегодный бюджет на обучение - 50,000 рублей на сотрудника. Покрывает курсы, книги, конференции. Требуется предварительное согласование с руководителем и HR. После обучения - отчет о применении полученных знаний."
    }
}

def get_available_slots_for_week() -> Dict[str, List[str]]:
    """Возвращает доступные слоты на эту неделю"""
    return AVAILABLE_SLOTS

def check_time_slot_availability(date: str, time: str, duration: int = 60) -> bool:
    """Проверяет доступность временного слота"""
    if date not in AVAILABLE_SLOTS:
        return False
    
    available_slots = AVAILABLE_SLOTS[date]
    requested_start = int(time.replace(":", ""))
    requested_end = requested_start + (duration // 60) * 100
    
    for slot in available_slots:
        start_time, end_time = slot.split("-")
        slot_start = int(start_time.replace(":", ""))
        slot_end = int(end_time.replace(":", ""))
        
        if slot_start <= requested_start and requested_end <= slot_end:
            return True
    
    return False

def book_meeting(date: str, time: str, title: str, duration: int = 60) -> Dict[str, Any]:
    """Симулирует бронирование встречи"""
    if check_time_slot_availability(date, time, duration):
        # В реальном приложении здесь была бы запись в базу данных
        return {
            "success": True,
            "message": f"Встреча '{title}' успешно запланирована на {date} в {time}",
            "meeting_id": f"meeting_{date}_{time}".replace(":", "").replace("-", "")
        }
    else:
        return {
            "success": False,
            "message": f"Временной слот {date} в {time} недоступен",
            "available_alternatives": AVAILABLE_SLOTS.get(date, [])
        }

def get_development_plan() -> Dict[str, Any]:
    """Возвращает индивидуальный план развития"""
    return DEVELOPMENT_PLAN

def search_corporate_regulations(query: str) -> List[Dict[str, str]]:
    """Поиск по корпоративным регламентам"""
    query_lower = query.lower()
    results = []
    
    for key, regulation in CORPORATE_REGULATIONS.items():
        if (query_lower in regulation["question"].lower() or 
            query_lower in regulation["answer"].lower()):
            results.append({
                "topic": key,
                "question": regulation["question"],
                "answer": regulation["answer"]
            })
    
    return results 