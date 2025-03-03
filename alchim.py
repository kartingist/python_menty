import matplotlib.pyplot as plt
from models import Session, Kline


def plot_symbol_history(symbol: str):
    """
    Извлекает данные свечей из БД для указанного символа и строит график изменения цены закрытия.
    """
    session = Session()
    # Получаем данные отсортированные по времени открытия
    klines = session.query(Kline).filter_by(symbol=symbol).order_by(Kline.open_time).all()
    session.close()

    if not klines:
        print("Нет данных для указанного символа.")
        return

    # Формируем списки для осей X (время) и Y (цена закрытия)
    times = [k.open_time for k in klines]
    closes = [k.close for k in klines]

    plt.figure(figsize=(10, 6))
    plt.plot(times, closes, label=f'{symbol} Цена закрытия', marker='o', linestyle='-')
    plt.title(f'История цены закрытия для {symbol}')
    plt.xlabel('Время')
    plt.ylabel('Цена закрытия (USD)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Пример использования:
plot_symbol_history("BTCUSDT")