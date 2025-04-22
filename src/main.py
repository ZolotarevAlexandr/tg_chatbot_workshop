import asyncio
import logging
import sys
from os import getenv

import dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from ollama import ChatResponse, chat

from src.db import Message, MessageRepository, init_db  # import classes and functions we just created

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

TOKEN = getenv("BOT_TOKEN")  # Replace with your actual token or use environment variable
MODEL_NAME = "llama3.2"  # Fine as long as we are working with only one model

# Initialize bot and dispatcher
dp = Dispatcher()
# Initialize the database connection
db_conn = init_db()
# Create repository instance with connection it will use. We will use that instance in the code
message_repo = MessageRepository(db_conn)


@dp.message(CommandStart())
async def start_handler(message: types.Message) -> None:
    """
    Handler for /start command. Resets conversation history for the user.
    """
    message_repo.delete_all_for_chat(message.chat.id)
    await message.answer("Hi! I'm AI chat bot")


@dp.message()
async def message_handler(message: types.Message) -> None:
    """
    Handler will send LLM response
    """
    try:
        # Create and save user message
        user_message = Message(chat_id=message.chat.id, role="user", content=message.text)
        message_repo.save(user_message)

        # Get recent messages
        recent_messages = message_repo.fetch_last_n(message.chat.id, 10)
        # Convert to format required by Ollama
        ollama_history = [msg.to_dict() for msg in recent_messages]

        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

        # Get response from LLM
        response: ChatResponse = chat(
            model=MODEL_NAME,
            messages=ollama_history,
        )

        # Create and save assistant message
        assistant_message = Message(chat_id=message.chat.id, role="assistant", content=response.message.content)
        message_repo.save(assistant_message)

        await message.answer(response.message.content)
    except Exception as e:
        logging.error(e)
        await message.answer("Error occurred during response generating")


async def main() -> None:
    # Initialize Bot instance
    bot = Bot(token=TOKEN)
    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
