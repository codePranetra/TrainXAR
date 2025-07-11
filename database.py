import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from config import (
    DB_HOST,
    DB_USER,  
    DB_PASSWORD,
    DB_NAME,
    DB_PORT
)
import logging
import datetime
import pytz

# MySQL Connection URL
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

ist = pytz.timezone('Asia/Calcutta')

Base = declarative_base()


class Message(Base):
    """
    Represents a chat message in the conversation history.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # e.g., "user", "assistant"
    content = Column(String, nullable=False)
    source = Column(String, nullable=False)
    is_deleted = Column(Integer, default=0)

    # --- NEW COLUMNS for media support ---
    # e.g. "document", "image", "audio", "voice", "sticker"
    media_type = Column(String, nullable=True)
    # local file path or an S3/URL to the stored file
    media_path = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(ist))


# Create engine and session
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """
    Initialize (create) the database tables if they do not exist.
    """
    Base.metadata.create_all(engine)


def get_db_session():
    return SessionLocal()


def store_message(user_id: str, role: str, content: str, source: str, 
                  media_type: str = None, media_path: str = None):
    """
    Store a single message in the database.
    """
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
        raise e
    finally:
        session.close()
        

def get_user_message(user_id):
    logging.info(f"🔍 Retrieving messages for user_id: {user_id} ")
    session = get_db_session()
    try:
        messages = session.query(Message)\
            .filter_by(user_id=user_id)\
            .order_by(Message.created_at)\
            .all()


        formatted_messages = []
        for message in messages:
            # Ensure media_path is not None before replacing
            
            formatted_messages.append({
                "id": message.id,
                "user_id": message.user_id,
                "role": message.role,
                "content": message.content,
                "media_type": message.media_type,
                "media_path": message.media_path,
                "source": message.source,
                "created_at": message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return formatted_messages

    finally:
        session.close()


def get_conversation_history(user_id: str,limit: int = None):
    """
    Retrieve a limited number of messages for a given user, sorted by creation time ascending.
    """
    session = get_db_session()
    try:
        query = session.query(Message).filter(
            Message.user_id == user_id,
        ).order_by(Message.created_at.desc())

        if limit is not None:
            query = query.limit(limit)

        messages = query.all()
        # Reverse the list so earliest message is first
        return messages[::-1]
    finally:
        session.close()




def get_media_path(user_id: str, bot_id: str,limit: int = None):
    """
    Retrieve a limited number of messages for a given user, sorted by creation time ascending.
    """
    session = get_db_session()
    try:
        query = session.query(Message).filter(
            Message.user_id == user_id,
            Message.bot_id == bot_id
        ).order_by(Message.created_at.desc())

        if limit is not None:
            query = query.limit(limit)

        messages = query.all()
        # Reverse the list so earliest message is first
        return messages[::-1]
    finally:
        session.close()
