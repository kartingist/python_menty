# schemas.py
from pydantic import BaseModel
from datetime import datetime

class KlineData(BaseModel):
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: datetime

    @classmethod
    def from_list(cls, data: list):
        """
        Преобразует список, полученный от Binance API, в объект KlineData.
        Ожидается, что data имеет вид:
        [
          Open time,
          Open,
          High,
          Low,
          Close,
          Volume,
          Close time,
          ...
        ]
        """
        return cls(
            open_time=datetime.fromtimestamp(data[0] / 1000),
            open=float(data[1]),
            high=float(data[2]),
            low=float(data[3]),
            close=float(data[4]),
            volume=float(data[5]),
            close_time=datetime.fromtimestamp(data[6] / 1000)
        )
