#!/usr/bin/env python3
"""
Test script for debugging the telegram bot AI processing
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our bot class
from telegram_bot_fastmcp import MCPTelegramBot, OllamaIntegration

async def test_ai_processing():
    """Test AI processing with debug mode"""
    print("🧪 Testing AI processing with debug mode...")
    
    # Create bot instance
    bot = MCPTelegramBot()
    
    # Initialize MCP server
    print("🔗 Initializing MCP server...")
    if not await bot.initialize_mcp():
        print("❌ Failed to initialize MCP server")
        return
    
    # Check Ollama
    print("🤖 Checking Ollama...")
    if not bot.ollama.check_ollama_availability():
        print("❌ Ollama not available")
        return
    
    # Set debug mode for test user
    test_user_id = 12345
    bot.user_debug_mode[test_user_id] = True
    
    # Test questions
    test_questions = [
        "Какие правила отпуска?",
        "Покажи дресс-код",
        "Запланируй встречу на завтра в 15:00 по проекту X"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*50}")
        print(f"ТЕСТ {i}: {question}")
        print('='*50)
        
        try:
            # Process with AI
            response = await bot.process_with_ai(test_user_id, question)
            print(f"\nОТВЕТ:\n{response}")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    asyncio.run(test_ai_processing()) 