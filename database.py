import datetime
import logging
import pytz

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Text
)
from sqlalchemy.orm import sessionmaker, declarative_base

from config import (
    DB_HOST,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
    DB_PORT
)

# ------------------------------------------------------------------
# Database configuration
# ------------------------------------------------------------------

DB_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?charset=utf8mb4"
)

engine = create_engine(
    DB_URL,
    echo=False,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

ist = pytz.timezone("Asia/Calcutta")

logging.basicConfig(level=logging.INFO)

# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------

class UserMeta(Base):
    __tablename__ = "user_meta"

    user_id = Column(String(255), primary_key=True)
    conversation_count = Column(Integer, default=0, nullable=False)
    gender = Column(String(20), default=None)
    fitnesswali_suggested = Column(Integer, default=0, nullable=False)  # 0 / 1


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(String(255), nullable=False, index=True)
    role = Column(String(20), nullable=False)          # user / assistant / system
    content = Column(Text, nullable=False)             # chat text
    source = Column(String(50), nullable=False)        # api / web / whatsapp etc.

    is_deleted = Column(Integer, default=0, nullable=False)

    media_type = Column(String(50), nullable=True)
    media_path = Column(String(512), nullable=True)

    created_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(ist),
        nullable=False
    )

# ------------------------------------------------------------------
# DB Init
# ------------------------------------------------------------------

def init_db():
    Base.metadata.create_all(engine)

# ------------------------------------------------------------------
# Session helper
# ------------------------------------------------------------------

def get_db_session():
    return SessionLocal()

# ------------------------------------------------------------------
# Message operations
# ------------------------------------------------------------------

def store_message(
    user_id: str,
    role: str,
    content: str,
    source: str,
    media_type: str = None,
    media_path: str = None
):
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


def get_user_message(user_id: str):
    session = get_db_session()
    try:
        messages = (
            session.query(Message)
            .filter(Message.user_id == user_id)
            .order_by(Message.created_at)
            .all()
        )

        return [
            {
                "id": m.id,
                "user_id": m.user_id,
                "role": m.role,
                "content": m.content,
                "media_type": m.media_type,
                "media_path": m.media_path,
                "source": m.source,
                "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for m in messages
        ]
    finally:
        session.close()


def get_conversation_history(user_id: str, limit: int = None):
    session = get_db_session()
    try:
        query = (
            session.query(Message.role, Message.content)
            .filter(Message.user_id == user_id)
            .order_by(Message.created_at.desc())
        )

        if limit:
            query = query.limit(limit)

        results = query.all()[::-1]

        return [{"role": r, "content": c} for r, c in results]
    finally:
        session.close()


def get_media_path(user_id: str, limit: int = None):
    session = get_db_session()
    try:
        query = (
            session.query(Message)
            .filter(Message.user_id == user_id)
            .order_by(Message.created_at.desc())
        )

        if limit:
            query = query.limit(limit)

        return query.all()[::-1]
    finally:
        session.close()

# ------------------------------------------------------------------
# User meta operations
# ------------------------------------------------------------------

def get_user_meta(user_id: str) -> dict | None:
    session = get_db_session()
    try:
        user = session.query(UserMeta).filter_by(user_id=user_id).first()
        if not user:
            return None

        return {
            "conversation_count": user.conversation_count,
            "gender": user.gender,
            "fitnesswali_suggested": bool(user.fitnesswali_suggested),
        }
    finally:
        session.close()


def update_user_meta(user_id: str, meta: dict):
    session = get_db_session()
    try:
        user = session.query(UserMeta).filter_by(user_id=user_id).first()
        if not user:
            user = UserMeta(user_id=user_id)

        user.conversation_count = meta.get(
            "conversation_count", user.conversation_count
        )
        user.gender = meta.get("gender", user.gender)
        user.fitnesswali_suggested = int(
            meta.get("fitnesswali_suggested", user.fitnesswali_suggested)
        )

        session.add(user)
        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to update user meta: {e}")
        raise
    finally:
        session.close()
