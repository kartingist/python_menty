# models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Asset(Base):
    __tablename__ = 'assets'
    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, nullable=False)  # например, BTCUSDT
    name = Column(String)
    amount = Column(Float, default=0.0)  # количество актива

class Kline(Base):
    __tablename__ = 'klines'
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False)
    open_time = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    close_time = Column(DateTime, nullable=False)

# Инициализация SQLite базы данных
engine = create_engine('sqlite:///portfolio.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
