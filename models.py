# models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Portfolio(Base):
    __tablename__ = 'portfolios'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)  # Название портфеля (логин)

class Asset(Base):
    __tablename__ = 'assets'
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False)  # например, BTCUSDT; убрал unique=True, так как теперь уникальность зависит от portfolio_id
    name = Column(String)
    amount = Column(Float, default=0.0)  # количество актива
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)  # Связь с портфелем

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