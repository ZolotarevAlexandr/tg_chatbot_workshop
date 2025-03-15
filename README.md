## Intro 

Here is tutorial file to help you along workshop or replicate everything later

That workshop is made by [one-zero-eight](https://t.me/one_zero_eight) for station on [InnoQuest](https://t.me/inno_quest) [event](https://t.me/inno_quest/66) 
Author of workshop: [@ZolotarevAlexandr](https://t.me/ZolotarevAlexandr). You can address all questions to me

Also, here is GitHub [link] for the code of the bot

## What are we going to do?

In short, make self-hosted telegram bot with LLM 

## What will we need?

Two things:
- Ollama for hosting LLM
- Python with `aiogram` library for wring bot itself and `ollama-python` library to connect Ollama and Python

So let's set everything up

Step 1. Let's install Ollama and make sure it's up and running:
- Install [Ollama](https://ollama.com/download)
- Check that it's installed by running `ollama -v` from console. It should output current version 
- Download LLM (we'll go with llama3.2, but feel free to try out [other models](https://ollama.com/search)) with `ollama pull llama3.2` 
- Once installed you should be able to start chat directly in the console with `ollama run llama3.2`

Step 2. Setup Telegram bot:
- Create new bot using [@BotFather](https://t.me/BotFather). Just send `/newbot` command and follow instructions 
- Create new Python project and install needed libraries with `pip install aiogram` and `pip install ollama`

But first of all, let's configure a project a bit:  
Essentially we need 2 things right now: `.env` file and `main.py` (in GitHub you'll find a bit more, but we can ignore them so far). Also, it's generally a nice idea to keep source code in `src` folder, separated from project config files. So, we want our project to look like:

```
project/
├── src/
│   └── main.py
│
└── .env
```

We need `.env` to keep environment variables such as bot token in our case (keeping that type of things as variables in code is pretty terrible idea).

To conveniently work with `.env` we will also install `dotenv` library which loads all variables from `.env` to environment variables so they are accessible with `os.getenv` function.

In `.env` we need only 1 line:
```
BOT_TOKEN=your_token
```
Where "your_token" to be replaced with token received from @BotFather

Now that we set up our project it's time to check that everything works by starting simple echo bot first:
```python 
import asyncio  
import logging  
import sys  
from os import getenv  
  
import dotenv  
from aiogram import Bot, Dispatcher, types  
  
dotenv.load_dotenv()  
  
# Configure logging  
logging.basicConfig(level=logging.INFO, stream=sys.stdout)  
  
# Bot token can be obtained via https://t.me/BotFather  
TOKEN = getenv("BOT_TOKEN")  # Replace with your actual token or use environment variable  
  
# Initialize dispatcher  
dp = Dispatcher()  
  
  
@dp.message()  
async def echo_handler(message: types.Message) -> None:  
    """  
    Handler will echo back any message to the sender    
    """    
    try:  
        # Send a copy of the received message  
        await message.answer(message.text)  
    except TypeError:  
        # Not all message types can be copied, so handle the exception  
        await message.answer("I can't echo this type of message!")  
  
  
async def main() -> None:  
    # Initialize Bot instance  
    bot = Bot(token=TOKEN)  
    # Start polling  
    await dp.start_polling(bot)  
  
  
if __name__ == "__main__":  
    asyncio.run(main())
```

If it sends back text messages you send it, everything works, and we are ready to start.

## How to connect Ollama and Python 

Ollama runs as a server on `http://localhost:11434` and has [nice API](https://github.com/ollama/ollama/blob/main/docs/api.md). But we won't even need it, because Ollama has official wrappers around its API for [Python](https://github.com/ollama/ollama-python) and [JS](https://github.com/ollama/ollama-js), that we've already installed, while setting Python project.

Main thing from Ollama library that we will need is `chat` function. Right now we are interested in 2 parameters of that function: `model` and `messages`. First is a string with model that we want to use, second is a list with chat history where each message represented as python dict:
```
{
    'role': 'user/assistant',
    'content': 'Message text',
}
```

It also takes other argument for formatting response, bool flag to receive it as a stream (by parts as response is being generated), feel free to experiment with them. 

Let's slightly change our echo bot to reply not with our text, but with LLM response and add handler for `/start` command.

```python 
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
  
  
@dp.message(CommandStart())  
async def start_handler(message: types.Message) -> None:  
    """  
    Handler for /start command.    
    """    
    await message.answer("Hi! I'm AI chat bot")  
  
  
@dp.message()  
async def message_handler(message: types.Message) -> None:  
    """  
    Handler will send LLM response    
    """    
    try:  
        # Set "typing" status while generating response to show user that message is being processed  
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")  
        # Get response from LLM  
        response: ChatResponse = chat(  
            model=MODEL_NAME,  
            messages=[{"role": "user", "content": message.text}],  
        )  
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
```

Now we successfully return LLM response to the user's message. But the problem is, we only let LLM know content of the last message. In other words, it doesn't know the context of the conversion. Let's fix it

Unfortunately, there is no convenient way to get message history of a bot, so we need to save user and bot messages somewhere. For the sake of simplicity we'll save them in dictionary so far.

```python 
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
```

Now we save user and bot message history and pass last 10 messages to LLM, so it's aware of conversation context. Also `/start` command now resets history.

## What's next?

Obviously, bot we've written is short (only about 80 lines), simple but really far from being perfect. Here is some stuff you can try to do next:
- Keep messages history in database instead of dictionary (you can try redis for that)
- Run everything inside a docker containers and connect with docker-compose 
- Try other models, let user choose model
- Add functionality to work with attached files 
- Try multimodal LLMs and add functionality to work with pictures
- Implement middleware layer that will determine which model to use for response, based on how complex request is

If you want to start bigger project with that, check [template](https://github.com/one-zero-eight/aiogram-template) for aiogram bots by one-zero-eight 
