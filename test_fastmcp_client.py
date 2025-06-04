#!/usr/bin/env python3
"""
Test Client for Educational MCP Server using FastMCP
Тестовый клиент для демонстрационного MCP-сервера с FastMCP
"""

import asyncio
import json
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def safe_json_parse(text):
    """Safely parse JSON string"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_text": text}


async def test_mcp_server():
    """Test the FastMCP server"""
    print("🧪 Testing Educational MCP Server with FastMCP...")
    
    # Create server parameters for stdio connection
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "mcp_server_fastmcp.py"],
        env=None
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("🔗 Connecting to MCP server...")
                
                # Initialize the connection
                await session.initialize()
                print("✅ Server initialized successfully!")
                
                # Test 1: List available tools
                print("\n📋 Testing tools listing...")
                tools = await session.list_tools()
                print(f"✅ Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"   - {tool.name}: {tool.description}")
                
                # Test 2: Call list_tools
                print("\n🔧 Testing list_tools...")
                result = await session.call_tool("list_tools", {})
                print("✅ list_tools result:")
                parsed = safe_json_parse(result.content[0].text)
                print(json.dumps(parsed, indent=2, ensure_ascii=False))
                
                # Test 3: Get available slots
                print("\n📅 Testing get_available_slots...")
                result = await session.call_tool("get_available_slots", {})
                print("✅ Available slots:")
                parsed = safe_json_parse(result.content[0].text)
                print(json.dumps(parsed, indent=2, ensure_ascii=False))
                
                # Test 4: Search regulations
                print("\n🔍 Testing search_regulations...")
                result = await session.call_tool("search_regulations", {"query": "отпуск"})
                print("✅ Regulations search result:")
                parsed = safe_json_parse(result.content[0].text)
                print(json.dumps(parsed, indent=2, ensure_ascii=False))
                
                # Test 5: Get development plan
                print("\n📈 Testing get_development_plan...")
                result = await session.call_tool("get_development_plan", {})
                print("✅ Development plan:")
                parsed = safe_json_parse(result.content[0].text)
                print(json.dumps(parsed, indent=2, ensure_ascii=False))
                
                # Test 6: Schedule a meeting
                print("\n📝 Testing schedule_meeting...")
                result = await session.call_tool("schedule_meeting", {
                    "date": "2024-01-15",
                    "time": "10:00", 
                    "title": "Test Meeting",
                    "duration": 30
                })
                print("✅ Meeting scheduled:")
                parsed = safe_json_parse(result.content[0].text)
                print(json.dumps(parsed, indent=2, ensure_ascii=False))
                
                # Test 7: List resources
                print("\n📚 Testing resources listing...")
                resources = await session.list_resources()
                print(f"✅ Found {len(resources.resources)} resources:")
                for resource in resources.resources:
                    print(f"   - {resource.uri}: {resource.name}")
                
                # Test 8: Read a resource
                print("\n📖 Testing resource reading...")
                from mcp.types import AnyUrl
                resource_content = await session.read_resource(AnyUrl("company://calendar/slots"))
                print("✅ Resource content:")
                parsed = safe_json_parse(resource_content.contents[0].text)
                print(json.dumps(parsed, indent=2, ensure_ascii=False))
                
                # Test 9: List prompts
                print("\n💭 Testing prompts listing...")
                prompts = await session.list_prompts()
                print(f"✅ Found {len(prompts.prompts)} prompts:")
                for prompt in prompts.prompts:
                    print(f"   - {prompt.name}: {prompt.description}")
                
                # Test 10: Get a prompt
                print("\n🎯 Testing prompt generation...")
                prompt = await session.get_prompt("career_advice", {
                    "current_role": "Junior Developer",
                    "goal": "стать Senior Developer"
                })
                print("✅ Generated prompt:")
                for i, message in enumerate(prompt.messages):
                    print(f"   Message {i+1} ({message.role}): {message.content.text}")
                
                print("\n🎉 All tests completed successfully!")
                
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


async def interactive_test():
    """Interactive testing mode"""
    print("🎮 Interactive MCP Server Testing Mode")
    print("Type 'help' for available commands, 'quit' to exit\n")
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "mcp_server_fastmcp.py"],
        env=None
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ Connected to MCP server!\n")
                
                while True:
                    try:
                        command = input("mcp> ").strip()
                        
                        if command == "quit":
                            break
                        elif command == "help":
                            print("""
Available commands:
  tools          - List all available tools
  resources      - List all available resources  
  prompts        - List all available prompts
  call <tool>    - Call a tool (will prompt for arguments)
  read <uri>     - Read a resource
  prompt <name>  - Get a prompt (will prompt for arguments)
  help           - Show this help message
  quit           - Exit
                            """)
                        elif command == "tools":
                            tools = await session.list_tools()
                            print(f"Available tools ({len(tools.tools)}):")
                            for tool in tools.tools:
                                print(f"  - {tool.name}: {tool.description}")
                        
                        elif command == "resources":
                            resources = await session.list_resources()
                            print(f"Available resources ({len(resources.resources)}):")
                            for resource in resources.resources:
                                print(f"  - {resource.uri}: {resource.name}")
                        
                        elif command == "prompts":
                            prompts = await session.list_prompts()
                            print(f"Available prompts ({len(prompts.prompts)}):")
                            for prompt in prompts.prompts:
                                print(f"  - {prompt.name}: {prompt.description}")
                        
                        elif command.startswith("call "):
                            tool_name = command[5:].strip()
                            if tool_name == "list_tools" or tool_name == "get_available_slots" or tool_name == "get_development_plan":
                                result = await session.call_tool(tool_name, {})
                                parsed = safe_json_parse(result.content[0].text)
                                print(json.dumps(parsed, indent=2, ensure_ascii=False))
                            elif tool_name == "search_regulations":
                                query = input("Enter search query: ")
                                result = await session.call_tool(tool_name, {"query": query})
                                parsed = safe_json_parse(result.content[0].text)
                                print(json.dumps(parsed, indent=2, ensure_ascii=False))
                            elif tool_name == "schedule_meeting":
                                date = input("Enter date (YYYY-MM-DD): ")
                                time = input("Enter time (HH:MM): ")
                                title = input("Enter meeting title: ")
                                duration = input("Enter duration in minutes (default 60): ") or "60"
                                result = await session.call_tool(tool_name, {
                                    "date": date, "time": time, "title": title, "duration": int(duration)
                                })
                                parsed = safe_json_parse(result.content[0].text)
                                print(json.dumps(parsed, indent=2, ensure_ascii=False))
                            else:
                                print(f"Unknown tool: {tool_name}")
                        
                        elif command.startswith("read "):
                            uri = command[5:].strip()
                            from mcp.types import AnyUrl
                            resource_content = await session.read_resource(AnyUrl(uri))
                            parsed = safe_json_parse(resource_content.contents[0].text)
                            print(json.dumps(parsed, indent=2, ensure_ascii=False))
                        
                        elif command.startswith("prompt "):
                            prompt_name = command[7:].strip()
                            if prompt_name == "career_advice":
                                current_role = input("Enter current role: ")
                                goal = input("Enter career goal: ")
                                prompt = await session.get_prompt(prompt_name, {
                                    "current_role": current_role, "goal": goal
                                })
                                for i, message in enumerate(prompt.messages):
                                    print(f"Message {i+1} ({message.role}): {message.content.text}")
                            elif prompt_name == "meeting_agenda":
                                meeting_type = input("Enter meeting type: ")
                                participants = input("Enter participants (optional): ") or "команда"
                                prompt = await session.get_prompt(prompt_name, {
                                    "meeting_type": meeting_type, "participants": participants
                                })
                                for i, message in enumerate(prompt.messages):
                                    print(f"Message {i+1} ({message.role}): {message.content.text}")
                            else:
                                print(f"Unknown prompt: {prompt_name}")
                        
                        elif command:
                            print(f"Unknown command: {command}. Type 'help' for available commands.")
                        
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        print(f"Error: {e}")
                
                print("\n👋 Goodbye!")
                
    except Exception as e:
        print(f"❌ Connection error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_test())
    else:
        asyncio.run(test_mcp_server()) 