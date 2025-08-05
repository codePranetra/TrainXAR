import os
import datetime
import pytz
import logging
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
class UserMeta(Base):
    __tablename__ = "user_meta"

    user_id = Column(String(255), primary_key=True)
    conversation_count = Column(Integer, default=0)
    gender = Column(String(20), default=None)  # or any suitable length
    fitnesswali_suggested = Column(Integer, default=0)  # Use 0/1 as boolean


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


logging.basicConfig(level=logging.INFO)


def get_conversation_history(user_id: str, limit: int = None):
    session = get_db_session()
    try:
        query = session.query(Message.role, Message.content).filter(
            Message.user_id == user_id
        ).order_by(Message.created_at.desc())

        if limit:
            query = query.limit(limit)

        results = query.all()[::-1]  # Reverse to oldest first


        # Return as list of dicts: {'role': ..., 'content': ...}
        return [{'role': role, 'content': content} for role, content in results]
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


# ------------------ SQLAlchemy: user_meta ------------------

def get_user_meta(user_id: str) -> dict:
    session = get_db_session()
    try:
        user = session.query(UserMeta).filter_by(user_id=user_id).first()
        if not user:
            return None
        return {
            "conversation_count": user.conversation_count,
            "gender": user.gender,
            "fitnesswali_suggested": bool(user.fitnesswali_suggested)
        }
    finally:
        session.close()


def update_user_meta(user_id: str, meta: dict):
    session = get_db_session()
    try:
        user = session.query(UserMeta).filter_by(user_id=user_id).first()
        if not user:
            user = UserMeta(user_id=user_id)

        user.conversation_count = meta.get("conversation_count", user.conversation_count or 0)
        user.gender = meta.get("gender", user.gender)
        user.fitnesswali_suggested = int(meta.get("fitnesswali_suggested", user.fitnesswali_suggested or 0))

        session.add(user)
        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to update user meta: {e}")
    finally:
        session.close()

