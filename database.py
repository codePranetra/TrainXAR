import os
import datetime
import pytz
import logging
import sqlite3

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from config import (
    DB_HOST,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
    DB_PORT
)

# MySQL Connection
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

ist = pytz.timezone('Asia/Calcutta')


# ------------------ SQLAlchemy Model ------------------

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    source = Column(String, nullable=False)
    is_deleted = Column(Integer, default=0)

    media_type = Column(String, nullable=True)
    media_path = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(ist))


# ------------------ DB Init ------------------

def init_db():
    Base.metadata.create_all(engine)

    # Initialize SQLite tables (for user_meta)
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            user_id TEXT,
            role TEXT,
            content TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_meta (
            user_id TEXT PRIMARY KEY,
            conversation_count INTEGER DEFAULT 0,
            is_female BOOLEAN DEFAULT 1,
            fitnesswali_suggested BOOLEAN DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()


# ------------------ SQLAlchemy Session ------------------

def get_db_session():
    return SessionLocal()


def store_message(user_id: str, role: str, content: str, source: str,
                  media_type: str = None, media_path: str = None):
    session = get_db_session()
    try:
        msg = Message(
            user_id=user_id,
            role=role,
            content=content,
            source=source,
            media_type=media_type,
            media_path=media_path
        )
        session.add(msg)
        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to store message: {e}")
        raise
    finally:
        session.close()


def get_user_message(user_id):
    logging.info(f"🔍 Retrieving messages for user_id: {user_id}")
    session = get_db_session()
    try:
        messages = session.query(Message)\
            .filter_by(user_id=user_id)\
            .order_by(Message.created_at)\
            .all()

        return [
            {
                "id": m.id,
                "user_id": m.user_id,
                "role": m.role,
                "content": m.content,
                "media_type": m.media_type,
                "media_path": m.media_path,
                "source": m.source,
                "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for m in messages
        ]
    finally:
        session.close()


def get_conversation_history(user_id: str, limit: int = None):
    session = get_db_session()
    try:
        query = session.query(Message).filter(
            Message.user_id == user_id
        ).order_by(Message.created_at.desc())

        if limit:
            query = query.limit(limit)

        return query.all()[::-1]  # Reverse to oldest first
    finally:
        session.close()


def get_media_path(user_id: str, bot_id: str = None, limit: int = None):
    session = get_db_session()
    try:
        query = session.query(Message).filter(
            Message.user_id == user_id
        )
        # Safe filter only if bot_id exists in table (currently it doesn't)
        if bot_id:
            logging.warning("⚠️ 'bot_id' not defined in Message model. Skipping filter.")

        query = query.order_by(Message.created_at.desc())

        if limit:
            query = query.limit(limit)

        return query.all()[::-1]
    finally:
        session.close()


# ------------------ SQLite: user_meta ------------------

def get_user_meta(user_id: str) -> dict:
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()

    cursor.execute("SELECT conversation_count, is_female, fitnesswali_suggested FROM user_meta WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "conversation_count": row[0],
            "is_female": bool(row[1]),
            "fitnesswali_suggested": bool(row[2])
        }
    return None


def update_user_meta(user_id: str, meta: dict):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO user_meta (user_id, conversation_count, is_female, fitnesswali_suggested)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            conversation_count = excluded.conversation_count,
            is_female = excluded.is_female,
            fitnesswali_suggested = excluded.fitnesswali_suggested;
    """, (
        user_id,
        meta.get("conversation_count", 0),
        int(meta.get("is_female", True)),
        int(meta.get("fitnesswali_suggested", False))
    ))

    conn.commit()
    conn.close()
