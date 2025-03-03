import matplotlib.pyplot as plt
import mplcursors
from models import Session, Kline
from config import conversion_rates, currency_symbols


def plot_symbol_history(symbol: str):
    """
    Извлекает данные свечей из БД для указанного символа и строит график изменения цены закрытия.
    При наведении на точку графика отображается стоимость в USD и других валютах,
    где для каждой валюты используется формат: "Код: <цена> <символ>".
    Окно графика получает заголовок с именем символа.
    """
    session = Session()
    klines = session.query(Kline).filter_by(symbol=symbol).order_by(Kline.open_time).all()
    session.close()

    if not klines:
        print("Нет данных для указанного символа.")
        return

    times = [k.open_time for k in klines]
    closes = [k.close for k in klines]

    # Создаём фигуру и устанавливаем заголовок окна
    fig = plt.figure(figsize=(10, 6))
    fig.canvas.manager.set_window_title(symbol)

    plt.plot(times, closes, label=f'{symbol} Цена закрытия', marker='o', linestyle='-', color='b')
    plt.title(f'История цены закрытия для {symbol}')
    plt.xlabel('Время')
    plt.ylabel(f'Цена закрытия ({currency_symbols["USD"]})')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    def get_price_in_other_currencies(price_usd):
        price_info = f'USD: {price_usd:,.2f} {currency_symbols["USD"]}'
        for curr, rate in conversion_rates.items():
            if curr != "USD":
                price_in_currency = price_usd * rate
                price_info += f'\n{curr}: {price_in_currency:,.2f} {currency_symbols.get(curr, curr)}'
        return price_info

    cursor = mplcursors.cursor(hover=True)
    cursor.connect("add", lambda sel: sel.annotation.set_text(get_price_in_other_currencies(closes[int(sel.index)])))

    plt.show()
