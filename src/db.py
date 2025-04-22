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


class Message:
    """
    Represents a message in a chat conversation.
    """

    def __init__(self, chat_id: int, role: str, content: str, message_id: int | None = None):
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
            "content": self.content,
        }


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
            (chat_id, n),
        )
        rows = cursor.fetchall()
        messages = [Message(chat_id=row[1], role=row[2], content=row[3], message_id=row[0]) for row in reversed(rows)]
        return messages

    def delete_all_for_chat(self, chat_id: int):
        """
        Delete all messages for a specific chat ID, used for resetting conversation.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM messages WHERE chat_id=?",
            (chat_id,),
        )
        self.conn.commit()
