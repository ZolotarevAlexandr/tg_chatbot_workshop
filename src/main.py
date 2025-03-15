import asyncio
import logging
import sys
from os import getenv

import dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from ollama import ChatResponse, chat

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

TOKEN = getenv("BOT_TOKEN")  # Replace with your actual token or use environment variable
MODEL_NAME = 'llama3.2' # Fine as long as we are working with only one model

# Initialize bot and dispatcher
dp = Dispatcher()

# Dictionary to store conversation history for each user
# Key: chat_id, Value: list of message objects
conversation_history = {}


@dp.message(CommandStart())
async def start_handler(message: types.Message) -> None:
    """
    Handler for /start command. Resets conversation history for the user.
    """
    conversation_history[message.chat.id] = []
    await message.answer("Hi! I'm AI chat bot")


@dp.message()
async def message_handler(message: types.Message) -> None:
    """
    Handler will send LLM response
    """
    try:
        if message.chat.id not in conversation_history:
            conversation_history[message.chat.id] = []

        # Add user message to history
        user_message = {"role": "user", "content": message.text}
        conversation_history[message.chat.id].append(user_message)

        # Get the last 10 messages
        recent_history = conversation_history[message.chat.id][-10:]

        # Set "typing" status while generating response to show user that message is being processed
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

        # Get response from LLM
        response: ChatResponse = chat(
            model=MODEL_NAME,
            messages=recent_history,
        )

        # Add assistant response to history
        assistant_message = {"role": "assistant", "content": response.message.content}
        conversation_history[message.chat.id].append(assistant_message)

        # Send user LLM response
        await message.answer(response.message.content)
    except Exception as e:
        # Handle errors, raised during response generation, we catch all exceptions since we handle them same way
        logging.error(e)
        await message.answer("Error occurred during response generating")


async def main() -> None:
    # Initialize Bot instance
    bot = Bot(token=TOKEN)
    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
