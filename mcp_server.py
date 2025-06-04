#!/usr/bin/env python3
"""
Educational MCP Server for Students
Демонстрационный MCP-сервер для обучающих целей
"""

import json
import sys
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from mcp_types import (
    Tool, Resource, Prompt, InitializeResult, ServerCapabilities, 
    JSONRPCResponse, TextContent, PromptMessage
)
from mock_data import (
    get_available_slots_for_week, book_meeting, get_development_plan, 
    search_corporate_regulations, AVAILABLE_SLOTS
)


class MCPServer:
    """Educational MCP Server Implementation"""
    
    def __init__(self):
        self.server_info = {
            "name": "educational-mcp-server",
            "version": "1.0.0"
        }
        
        # Определяем доступные инструменты
        self.tools = [
            Tool(
                name="list_tools",
                description="Показать список всех доступных инструментов с описанием",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_available_slots",
                description="Получить доступные временные слоты на текущую неделю",
                inputSchema={
                    "type": "object", 
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="schedule_meeting",
                description="Запланировать встречу на определенную дату и время",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Дата встречи в формате YYYY-MM-DD"
                        },
                        "time": {
                            "type": "string", 
                            "description": "Время встречи в формате HH:MM"
                        },
                        "title": {
                            "type": "string",
                            "description": "Название встречи"
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Продолжительность в минутах (по умолчанию 60)",
                            "default": 60
                        }
                    },
                    "required": ["date", "time", "title"]
                }
            ),
            Tool(
                name="get_development_plan",
                description="Получить индивидуальный план развития в компании",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="search_regulations",
                description="Найти информацию по корпоративным регламентам",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Поисковый запрос по регламентам"
                        }
                    },
                    "required": ["query"]
                }
            )
        ]
        
        self.capabilities = ServerCapabilities(
            tools={"listChanged": True},
            resources={"subscribe": True, "listChanged": True},
            prompts={"listChanged": True}
        )

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка входящих JSON-RPC запросов"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "tools/list":
                result = self._handle_list_tools()
            elif method == "tools/call":
                result = await self._handle_call_tool(params)
            elif method == "resources/list":
                result = self._handle_list_resources()
            elif method == "resources/read":
                result = self._handle_read_resource(params)
            elif method == "prompts/list":
                result = self._handle_list_prompts()
            elif method == "prompts/get":
                result = self._handle_get_prompt(params)
            else:
                return self._create_error_response(request_id, -32601, f"Method not found: {method}")
                
            return JSONRPCResponse(id=request_id, result=result).dict()
            
        except Exception as e:
            return self._create_error_response(request_id, -32603, f"Internal error: {str(e)}")

    def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка запроса инициализации"""
        return InitializeResult(
            protocolVersion="2024-11-05",
            capabilities=self.capabilities,
            serverInfo=self.server_info
        ).dict()

    def _handle_list_tools(self) -> Dict[str, Any]:
        """Возвращает список доступных инструментов"""
        return {"tools": [tool.dict() for tool in self.tools]}

    async def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка вызова инструмента"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "list_tools":
            return await self._tool_list_tools()
        elif tool_name == "get_available_slots":
            return await self._tool_get_available_slots()
        elif tool_name == "schedule_meeting":
            return await self._tool_schedule_meeting(arguments)
        elif tool_name == "get_development_plan":
            return await self._tool_get_development_plan()
        elif tool_name == "search_regulations":
            return await self._tool_search_regulations(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _tool_list_tools(self) -> Dict[str, Any]:
        """Инструмент: Список всех доступных инструментов"""
        tools_info = []
        for tool in self.tools:
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": list(tool.inputSchema.get("properties", {}).keys())
            })
        
        return {
            "content": [
                TextContent(text=json.dumps({
                    "available_tools": tools_info,
                    "total_count": len(tools_info),
                    "description": "Полный список доступных инструментов MCP сервера"
                }, ensure_ascii=False, indent=2)).dict()
            ]
        }

    async def _tool_get_available_slots(self) -> Dict[str, Any]:
        """Инструмент: Получить доступные слоты"""
        slots = get_available_slots_for_week()
        
        formatted_slots = []
        for date, times in slots.items():
            if times:  # Только дни с доступными слотами
                formatted_slots.append({
                    "date": date,
                    "available_times": times,
                    "day_of_week": datetime.strptime(date, "%Y-%m-%d").strftime("%A")
                })
        
        return {
            "content": [
                TextContent(text=json.dumps({
                    "available_slots": formatted_slots,
                    "note": "Все времена указаны в московском часовом поясе",
                    "booking_instruction": "Для записи используйте инструмент 'schedule_meeting'"
                }, ensure_ascii=False, indent=2)).dict()
            ]
        }

    async def _tool_schedule_meeting(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Инструмент: Запланировать встречу"""
        date = arguments.get("date")
        time = arguments.get("time") 
        title = arguments.get("title")
        duration = arguments.get("duration", 60)
        
        result = book_meeting(date, time, title, duration)
        
        return {
            "content": [
                TextContent(text=json.dumps(result, ensure_ascii=False, indent=2)).dict()
            ]
        }

    async def _tool_get_development_plan(self) -> Dict[str, Any]:
        """Инструмент: Получить план развития"""
        plan = get_development_plan()
        
        return {
            "content": [
                TextContent(text=json.dumps(plan, ensure_ascii=False, indent=2)).dict()
            ]
        }

    async def _tool_search_regulations(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Инструмент: Поиск по регламентам"""
        query = arguments.get("query", "")
        
        if not query:
            return {
                "content": [
                    TextContent(text="Ошибка: Необходимо указать поисковый запрос").dict()
                ]
            }
        
        results = search_corporate_regulations(query)
        
        if not results:
            return {
                "content": [
                    TextContent(text=json.dumps({
                        "message": "По вашему запросу ничего не найдено",
                        "suggestion": "Попробуйте использовать ключевые слова: отпуск, больничный, дресс-код, удаленка, обучение, оборудование"
                    }, ensure_ascii=False, indent=2)).dict()
                ]
            }
        
        return {
            "content": [
                TextContent(text=json.dumps({
                    "search_query": query,
                    "results": results,
                    "found_count": len(results)
                }, ensure_ascii=False, indent=2)).dict()
            ]
        }

    def _handle_list_resources(self) -> Dict[str, Any]:
        """Возвращает список доступных ресурсов"""
        resources = [
            Resource(
                uri="company://calendar/slots",
                name="Available Time Slots",
                description="Доступные временные слоты для встреч",
                mimeType="application/json"
            ),
            Resource(
                uri="company://development/plan",
                name="Development Plan", 
                description="Индивидуальный план развития",
                mimeType="application/json"
            ),
            Resource(
                uri="company://regulations/all",
                name="Corporate Regulations",
                description="Корпоративные регламенты и политики",
                mimeType="application/json"
            )
        ]
        
        return {"resources": [resource.dict() for resource in resources]}

    def _handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Чтение ресурса по URI"""
        uri = params.get("uri")
        
        if uri == "company://calendar/slots":
            content = json.dumps(get_available_slots_for_week(), ensure_ascii=False, indent=2)
        elif uri == "company://development/plan":
            content = json.dumps(get_development_plan(), ensure_ascii=False, indent=2)
        elif uri == "company://regulations/all":
            content = json.dumps({"regulations": search_corporate_regulations("")}, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"Unknown resource URI: {uri}")
        
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": content
                }
            ]
        }

    def _handle_list_prompts(self) -> Dict[str, Any]:
        """Возвращает список доступных промптов"""
        prompts = [
            Prompt(
                name="career_advice",
                description="Получить совет по карьерному развитию",
                arguments=[
                    {"name": "current_role", "description": "Текущая должность", "required": True},
                    {"name": "goal", "description": "Карьерная цель", "required": True}
                ]
            ),
            Prompt(
                name="meeting_agenda",
                description="Создать повестку дня для встречи",
                arguments=[
                    {"name": "meeting_type", "description": "Тип встречи", "required": True},
                    {"name": "participants", "description": "Участники", "required": False}
                ]
            )
        ]
        
        return {"prompts": [prompt.dict() for prompt in prompts]}

    def _handle_get_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Получение промпта по имени"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if name == "career_advice":
            current_role = arguments.get("current_role", "")
            goal = arguments.get("goal", "")
            
            messages = [
                PromptMessage(
                    role="system",
                    content=f"Ты карьерный консультант. Помоги сотруднику в должности '{current_role}' достичь цели '{goal}'"
                ),
                PromptMessage(
                    role="user", 
                    content=f"Я работаю {current_role} и хочу {goal}. Какие шаги мне предпринять?"
                )
            ]
        elif name == "meeting_agenda":
            meeting_type = arguments.get("meeting_type", "")
            participants = arguments.get("participants", "команда")
            
            messages = [
                PromptMessage(
                    role="system",
                    content="Ты помощник для создания повесток дня встреч"
                ),
                PromptMessage(
                    role="user",
                    content=f"Создай повестку дня для встречи типа '{meeting_type}' с участниками: {participants}"
                )
            ]
        else:
            raise ValueError(f"Unknown prompt: {name}")
        
        return {
            "description": f"Промпт для {name}",
            "messages": [msg.dict() for msg in messages]
        }

    def _create_error_response(self, request_id: Optional[str], code: int, message: str) -> Dict[str, Any]:
        """Создание ответа с ошибкой"""
        return JSONRPCResponse(
            id=request_id,
            error={"code": code, "message": message}
        ).dict()


async def main():
    """Основная функция сервера"""
    server = MCPServer()
    
    print("🚀 Educational MCP Server started!", file=sys.stderr)
    print("📚 Это демонстрационный сервер для обучения студентов", file=sys.stderr)
    print("🔧 Доступные инструменты:", file=sys.stderr)
    for tool in server.tools:
        print(f"   - {tool.name}: {tool.description}", file=sys.stderr)
    print("", file=sys.stderr)
    
    try:
        while True:
            # Читаем JSON-RPC запрос из stdin
            line = sys.stdin.readline()
            if not line:
                break
                
            try:
                request = json.loads(line.strip())
                response = await server.handle_request(request)
                
                # Отправляем ответ в stdout
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                error_response = server._create_error_response(
                    None, -32700, f"Parse error: {str(e)}"
                )
                print(json.dumps(error_response), flush=True)
                
    except KeyboardInterrupt:
        print("👋 Educational MCP Server stopped", file=sys.stderr)
    except Exception as e:
        print(f"❌ Server error: {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main()) 