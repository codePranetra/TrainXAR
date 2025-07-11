import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv,find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Configuration from .env
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

# MySQL Connection URL
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create Engine
engine = create_engine(DB_URL, echo=False)

# Session Local
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base Model
Base = declarative_base()


scheduler_engine = create_engine(
    DB_URL,
    pool_pre_ping=True,    # test before use, auto‑reconnect transparently
    pool_recycle=3600,     # recycle anything >1 h old
)

SessionLocal_scheduler = sessionmaker(bind=scheduler_engine)



def get_db():
    """ Dependency function to get the database session """
    with SessionLocal() as session:
        yield session

def get_database_name():
    """ Fetch the currently connected database name """
    with SessionLocal() as session:
        try:
            result = session.execute("SELECT DATABASE();")
            db_name = result.scalar()
            return f"Connected to Database: {db_name}"
        except Exception as e:
            return f"Error fetching database name: {e}"
