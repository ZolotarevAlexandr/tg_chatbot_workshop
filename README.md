## Intro 

Here is tutorial file to help you along workshop or replicate everything later

That workshop is made by [one-zero-eight](https://t.me/one_zero_eight) for station on [InnoQuest](https://t.me/inno_quest) [event](https://t.me/inno_quest/66) 
Author of workshop: [@ZolotarevAlexandr](https://t.me/ZolotarevAlexandr). You can address all questions to me

Also, here is GitHub [link](https://github.com/ZolotarevAlexandr/tg_chatbot_workshop) for the code of the bot

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
```dotenv
BOT_TOKEN=your_token
```
Where "your_token" to be replaced with token received from @BotFather

Now that we set up our project it's time to check that everything works by starting simple echo bot first:
```python 
# main.py
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
# main.py
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
# main.py
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


## Adding database

Obviously, keeping messages in a code variable isn't a greate idea, so we need a database.  
We'll use sqlite as it pretty simple to set up and needed libraries are already
included in Python so we don't need to install anything extra. 

Sqlite is file-based db so let's add path to it to
.env file:
```dotenv
BOT_TOKEN=7574899113:AAEHWTAp8scsVjvdWkz-prYAwFSDtrOssMM
DB_PATH=db/messages.sqlite
```

And create a new `db.py` file for functionality related to db:
```
project/
├── src/
│   ├── main.py
│   └── db.py
│
└── .env
```

Fist things first, we need function that will create necessary tables (if they don't exist) and
return connection to the database:
```python
# db.py
import logging
import os
import sqlite3

from dotenv import load_dotenv

load_dotenv()

# Get database path from environment variable
db_relative_path = os.getenv("DB_PATH")

# Get the path to the project root (parent of src directory)
src_dir = os.path.dirname(os.path.abspath(__file__))  # src directory
project_root = os.path.dirname(src_dir)  # parent of src (project root)

# Construct absolute path to database
db_absolute_path = os.path.join(project_root, db_relative_path)

# Create directory if it doesn't exist
os.makedirs(os.path.dirname(db_absolute_path), exist_ok=True)


# Initialize database connection, creates tables if they don't exist
def init_db():
    logging.info(f"Connecting to database: {db_absolute_path}")
    conn = sqlite3.connect(db_absolute_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn
```
What's going on here? Well first we get path of the database
When developing a project all paths are usually defined
from project root. But our script is started from `src`. So to find
path we actually want we need to get path of `src` first.
Also, while `sqlite3` can create file of the database if it's missing it
doesn't create paths leading to it, so we need to create needed directories first

In the code you can notice two main object of sqlite3 library: connection and cursor.  
The Connection manages the database link, while the Cursor handles query execution and result retrieval

Now that we have a database, it would be a good idea to create a class that 
will represent object in database as Python object. Here we will not touch ORM (Object-Relational Mapping) models
to keep things simple and practice SQL a little bit.
```python
# db.py
class Message:
    """
    Represents a message in a chat conversation.
    """
    def __init__(self, chat_id: int, role: str, content: str, message_id: int = None):
        """
        Initialize a Message object with chat info and optional ID.
        """
        self.message_id = message_id
        self.chat_id = chat_id
        self.role = role
        self.content = content

    def to_dict(self):
        """
        Convert message to a dictionary format for Ollama API.
        """
        return {
            "role": self.role,
            "content": self.content
        }
```
In that class we reflect all db columns as class fields and 
add `to_dict` method for converting class to dictionary that can
be later converted to API-compatible json.

Alright, we have a model, now we need some functions to actually add, edit, delete, etc. in db
objects of that class.
To keep model and db logic separated, let's create one more class: `MessageRepository`
that will be responsible for changing object of `Message` class in db:
```python
# db.py
class MessageRepository:
    """
    Handles database operations for Message objects.
    """
    def __init__(self, connection: sqlite3.Connection):
        """
        Initialize repository with a database connection.
        """
        self.conn = connection

    def save(self, message: Message):
        """
        Save a message to the database, creating or updating as needed.
        """
        cursor = self.conn.cursor()
        if message.message_id is None:
            cursor.execute(
                "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
                (message.chat_id, message.role, message.content),
            )
            message.message_id = cursor.lastrowid
        else:
            cursor.execute(
                "UPDATE messages SET chat_id=?, role=?, content=? WHERE id=?",
                (message.chat_id, message.role, message.content, message.message_id),
            )
        self.conn.commit()
        return message

    def fetch_last_n(self, chat_id: int, n: int):
        """
        Retrieve the last N messages from a specific chat.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, chat_id, role, content FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT ?",
            (chat_id, n)
        )
        rows = cursor.fetchall()
        messages = [Message(chat_id=row[1], role=row[2], content=row[3], message_id=row[0])
                   for row in reversed(rows)]
        return messages

    def delete_all_for_chat(self, chat_id: int):
        """
        Delete all messages for a specific chat ID, used for resetting conversation.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
        self.conn.commit()
```
So far we only have methods we need, but we can easily add new ones.

Now that we have all necessary things to work with database, let's edit our bot:
```python
# main.py
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
```

Congratulations, now bot uses database for keeping messages and will not lose them
if you'll need to restart it.

## What to do next?

Obviously, bot right now is pretty small and there is a room for improvement. 
Here is some stuff you can try to do next:
- Try other models, let user choose model
- Try multimodal LLMs and add functionality to work with pictures
- Implement middleware layer that will determine which model to use for response, based on request
- Add ORM (like sqlalchemy) for working with database, instead of "raw" SQL
- Run everything inside a Docker container
- Host your project on a server

(It can be part 2, if liked this one)

## Useful links
- [Ollama documentation and examples](https://github.com/ollama/ollama-python/tree/main/examples)
- [Ollama-python documentation and examples](https://github.com/ollama/ollama-python/tree/main/examples)
- [Template for aiogram bots](https://github.com/one-zero-eight/aiogram-template.git)
- [Larger aiogram bot](https://github.com/one-zero-eight/music-room.git)
- [Implementation of messages with ORM](https://github.com/one-zero-eight/hackathon-integration-platform.git)
