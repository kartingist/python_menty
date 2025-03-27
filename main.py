# main.py
import csv
import os
from models import Session, Kline, Asset, Portfolio  # Обновленный импорт
from schemas import KlineData
from binance_api_client import BinanceClient
from rich.console import Console
from rich.table import Table
from rich.progress import track
from config import conversion_rates, currency_symbols
from plot_visualization import plot_symbol_history

console = Console(width=200)

# Глобальный словарь валютных курсов относительно 1 USD
# Изначально можно задать примерные значения, они будут обновлены с Binance.

# Словарь с именами активов для отображения (при просмотре деталей)
asset_names = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "BNB": "Binance Coin",
    "ADA": "Cardano",
    "XRP": "Ripple",
    "DOGE": "Dogecoin",
}


class PortfolioManager:
    def __init__(self):
        self.session = Session()
        self.current_portfolio = None

    def select_portfolio(self):
        """Выбор или создание портфеля по названию."""
        while True:
            portfolio_name = input("Введите название портфеля (логин): ").strip()
            if not portfolio_name:
                console.print("[red]Название портфеля не может быть пустым.[/red]")
                continue

            portfolio = self.session.query(Portfolio).filter_by(name=portfolio_name).first()
            if portfolio:
                self.current_portfolio = portfolio
                console.print(f"[green]Выбран портфель: {portfolio_name}[/green]")
                break
            else:
                create_new = input(f"Портфель '{portfolio_name}' не найден. Создать новый? (y/n): ").strip().lower()
                if create_new == 'y':
                    new_portfolio = Portfolio(name=portfolio_name)
                    self.session.add(new_portfolio)
                    self.session.commit()
                    self.current_portfolio = new_portfolio
                    console.print(f"[green]Создан и выбран новый портфель: {portfolio_name}[/green]")
                    break
                else:
                    console.print("[yellow]Пожалуйста, выберите существующий портфель или создайте новый.[/yellow]")

    def get_current_portfolio_id(self):
        """Возвращает ID текущего портфеля."""
        if not self.current_portfolio:
            raise ValueError("Портфель не выбран!")
        return self.current_portfolio.id

    def close(self):
        """Закрытие сессии."""
        self.session.close()


def get_fiat_rate(fiat: str) -> float:
    client = BinanceClient()
    symbol1 = "USDT" + fiat
    data1 = client._send_request("GET", "/api/v3/ticker/price", params={"symbol": symbol1})
    if "price" in data1:
        try:
            rate = float(data1["price"])
            return rate  # 1 USDT = rate FIAT
        except Exception:
            pass
    symbol2 = fiat + "USDT"
    data2 = client._send_request("GET", "/api/v3/ticker/price", params={"symbol": symbol2})
    if "price" in data2:
        try:
            rate = float(data2["price"])
            return 1 / rate if rate != 0 else None
        except Exception:
            pass
    return None


def update_all_fiat_rates_from_binance():
    global conversion_rates
    for fiat in conversion_rates:
        if fiat == "USD":
            continue
        rate = get_fiat_rate(fiat)
        if rate is not None:
            conversion_rates[fiat] = rate
        else:
            console.print(f"[red]Не удалось обновить курс для {fiat}.[/red]")
    console.print("[green]Курсы обмена обновлены на основе данных с Binance.[/green]")


def view_exchange_rates():
    update_all_fiat_rates_from_binance()
    table = Table(title="Курсы обмена (1 USD = ?)")
    table.add_column("Валюта", style="cyan", justify="center")
    table.add_column("Курс", style="magenta", justify="center")
    for curr, rate in conversion_rates.items():
        table.add_row(curr, f"{rate:,.4f}")
    console.print(table)


def fetch_and_store_klines(symbol: str, interval: str, limit: int = 500):
    console.print(f"[bold blue]Запрос исторических данных для {symbol} с интервалом {interval}...[/bold blue]")
    client = BinanceClient()
    raw_data = client.get_klines(symbol, interval, limit=limit)

    session = Session()
    new_count = 0

    for entry in track(raw_data, description="Обработка записей..."):
        try:
            kline_data = KlineData.from_list(entry)
            exists = session.query(Kline).filter_by(symbol=symbol, open_time=kline_data.open_time).first()
            if not exists:
                kline_entry = Kline(
                    symbol=symbol,
                    open_time=kline_data.open_time,
                    open=kline_data.open,
                    high=kline_data.high,
                    low=kline_data.low,
                    close=kline_data.close,
                    volume=kline_data.volume,
                    close_time=kline_data.close_time
                )
                session.add(kline_entry)
                new_count += 1
        except Exception as e:
            console.print(f"[red]Ошибка обработки записи: {e}[/red]")
    session.commit()
    session.close()
    console.print(f"[green]Сохранено {new_count} новых записей для {symbol}.[/green]")


def analyze_klines(symbol: str):
    session = Session()
    klines = session.query(Kline).filter_by(symbol=symbol).all()
    if not klines:
        console.print("[red]Нет данных для анализа.[/red]")
        session.close()
        return None

    total_close = sum(k.close for k in klines)
    avg_close = total_close / len(klines)
    max_close = max(k.close for k in klines)
    min_close = min(k.close for k in klines)
    session.close()

    analysis = {
        'symbol': symbol,
        'data_points': len(klines),
        'avg_close': avg_close,
        'max_close': max_close,
        'min_close': min_close
    }
    return analysis


def display_analysis(analysis: dict):
    table = Table(title="Анализ исторических данных")
    table.add_column("Параметр", style="cyan", justify="right")
    table.add_column("Значение", style="magenta")
    for key, value in analysis.items():
        table.add_row(key, str(value))
    console.print(table)


def export_analysis(analysis: dict, filename: str):
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['symbol', 'data_points', 'avg_close', 'max_close', 'min_close']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(analysis)
    console.print(f"[green]Аналитика экспортирована в файл {filename}.[/green]")


# ------------- Функции для управления портфелем -------------

def view_portfolio(manager: PortfolioManager):
    update_all_fiat_rates_from_binance()
    session = Session()
    portfolio_id = manager.get_current_portfolio_id()
    assets = session.query(Asset).filter_by(portfolio_id=portfolio_id).all()
    if not assets:
        console.print(f"[yellow]Портфель '{manager.current_portfolio.name}' пуст.[/yellow]")
        session.close()
        return

    client = BinanceClient()
    table = Table(title=f"Портфель: {manager.current_portfolio.name}", expand=True)
    table.add_column("Символ", style="cyan", no_wrap=True)
    table.add_column("Название", style="magenta", no_wrap=False)
    table.add_column("Количество", style="green", justify="right", no_wrap=True)
    table.add_column("Цена (USD)", justify="right", no_wrap=True)
    table.add_column("Стоимость (USD)", justify="right", no_wrap=True)

    additional_currency_columns = [curr for curr in conversion_rates if curr != "USD"]
    for curr in additional_currency_columns:
        table.add_column(f"Стоимость ({curr})", justify="right", no_wrap=False, overflow="fold")

    totals = {curr: 0.0 for curr in conversion_rates}

    for asset in assets:
        data = client._send_request('GET', '/api/v3/ticker/price', params={'symbol': asset.symbol})
        price_usd = float(data.get("price", 0)) if "price" in data else 0.0
        value_usd = asset.amount * price_usd
        totals["USD"] += value_usd

        cost_values = []
        for curr in additional_currency_columns:
            rate = conversion_rates[curr]
            cost = value_usd * rate
            totals[curr] += cost
            cost_values.append(f"{curr}: {cost:,.2f} {currency_symbols.get(curr, curr)}")

        table.add_row(
            asset.symbol,
            asset.name or "N/A",
            str(asset.amount),
            f"USD: {price_usd:,.2f} {currency_symbols['USD']}",
            f"USD: {value_usd:,.2f} {currency_symbols['USD']}",
            *cost_values
        )

    total_row = ["[bold]Итого[/bold]", "", "", "", f"[bold]USD: {totals['USD']:,.2f} {currency_symbols['USD']}[/bold]"]
    for curr in additional_currency_columns:
        total_row.append(f"[bold]{curr}: {totals[curr]:,.2f} {currency_symbols.get(curr, curr)}[/bold]")
    table.add_row(*total_row)

    console.print(table)
    session.close()


def add_asset(manager: PortfolioManager):
    session = Session()
    symbol = input("Введите символ актива (например, BTCUSDT): ").strip().upper()
    name = input("Введите название актива: ").strip()
    try:
        amount = float(input("Введите количество актива: "))
    except ValueError:
        console.print("[red]Неверное значение количества.[/red]")
        session.close()
        return
    portfolio_id = manager.get_current_portfolio_id()
    asset = session.query(Asset).filter_by(symbol=symbol, portfolio_id=portfolio_id).first()
    if asset:
        console.print(f"[yellow]Актив {symbol} уже существует в портфеле '{manager.current_portfolio.name}'.[/yellow]")
    else:
        new_asset = Asset(symbol=symbol, name=name, amount=amount, portfolio_id=portfolio_id)
        session.add(new_asset)
        session.commit()
        console.print(f"[green]Актив {symbol} добавлен в портфель '{manager.current_portfolio.name}'.[/green]")
    session.close()


def update_asset(manager: PortfolioManager):
    session = Session()
    symbol = input("Введите символ актива для обновления: ").strip().upper()
    portfolio_id = manager.get_current_portfolio_id()
    asset = session.query(Asset).filter_by(symbol=symbol, portfolio_id=portfolio_id).first()
    if not asset:
        console.print(f"[red]Актив {symbol} не найден в портфеле '{manager.current_portfolio.name}'.[/red]")
        session.close()
        return
    try:
        new_amount = float(input("Введите новое количество актива: "))
    except ValueError:
        console.print("[red]Неверное значение количества.[/red]")
        session.close()
        return
    asset.amount = new_amount
    session.commit()
    console.print(f"[green]Актив {symbol} успешно обновлён в портфеле '{manager.current_portfolio.name}'.[/green]")
    session.close()


def remove_asset(manager: PortfolioManager):
    session = Session()
    symbol = input("Введите символ актива для удаления: ").strip().upper()
    portfolio_id = manager.get_current_portfolio_id()
    asset = session.query(Asset).filter_by(symbol=symbol, portfolio_id=portfolio_id).first()
    if not asset:
        console.print(f"[red]Актив {symbol} не найден в портфеле '{manager.current_portfolio.name}'.[/red]")
        session.close()
        return
    session.delete(asset)
    session.commit()
    console.print(f"[green]Актив {symbol} удалён из портфеля '{manager.current_portfolio.name}'.[/green]")
    session.close()


def view_all_exchange_assets():
    console.print("[bold blue]Запрос информации о бирже...[/bold blue]")
    client = BinanceClient()
    exchange_info = client._send_request('GET', '/api/v3/exchangeInfo')
    symbols = exchange_info.get("symbols", [])
    if not symbols:
        console.print("[red]Не удалось получить данные о бирже.[/red]")
        return

    table = Table(title="Доступные активы (торговые пары)")
    table.add_column("Символ", style="cyan", no_wrap=True)
    table.add_column("Базовый актив", style="magenta")
    table.add_column("Котируемый актив", style="green")
    table.add_column("Статус", style="yellow")
    for sym in symbols:
        table.add_row(
            sym.get("symbol", "N/A"),
            sym.get("baseAsset", "N/A"),
            sym.get("quoteAsset", "N/A"),
            sym.get("status", "N/A")
        )
    console.print(table)


def view_asset_details():
    symbol = input("Введите символ актива для просмотра деталей (например, BTCUSDT): ").strip().upper()
    client = BinanceClient()
    data = client._send_request('GET', '/api/v3/ticker/price', params={'symbol': symbol})
    if "price" not in data:
        console.print(f"[red]Не удалось получить данные для {symbol}.[/red]")
        return
    try:
        price_usd = float(data["price"])
    except ValueError:
        console.print("[red]Некорректная цена, полученная от API.[/red]")
        return

    if symbol.endswith("USDT"):
        base_asset = symbol[:-4]
    else:
        base_asset = symbol

    full_name = asset_names.get(base_asset, base_asset)
    price_in_rates = {}
    for curr, rate in conversion_rates.items():
        price_in_rates[curr] = price_usd * rate

    table = Table(title=f"Детали актива {symbol}")
    table.add_column("Параметр", style="cyan", justify="right")
    table.add_column("Значение", style="magenta")
    table.add_row("Символ", symbol)
    table.add_row("Название", full_name)
    table.add_row("Цена (USD)", f"${price_usd:,.2f}")
    for curr, price in price_in_rates.items():
        if curr != "USD":
            table.add_row(f"Цена ({curr})", f"{price:,.2f} {curr}")
    console.print(table)


def edit_asset_names():
    global asset_names
    console.print("[bold blue]Текущий список названий активов:[/bold blue]")
    for code, name in asset_names.items():
        console.print(f"{code}: {name}")
    console.print("\n[bold blue]Меню редактирования:[/bold blue]")
    console.print("[cyan]1.[/cyan] Добавить/обновить название актива")
    console.print("[cyan]2.[/cyan] Удалить запись")
    console.print("[cyan]3.[/cyan] Выход")
    choice = input("Выберите опцию: ").strip()
    if choice == "1":
        code = input("Введите код базового актива (например, BTC): ").strip().upper()
        name = input("Введите полное название: ").strip()
        asset_names[code] = name
        console.print(f"[green]Запись обновлена: {code} - {name}[/green]")
    elif choice == "2":
        code = input("Введите код базового актива для удаления: ").strip().upper()
        if code in asset_names:
            del asset_names[code]
            console.print(f"[green]Запись для {code} удалена.[/green]")
        else:
            console.print(f"[yellow]Запись для {code} не найдена.[/yellow]")
    elif choice == "3":
        console.print("[bold green]Выход из редактирования.[/bold green]")
    else:
        console.print("[red]Неверный выбор.[/red]")


def interactive_portfolio_management(manager: PortfolioManager):
    while True:
        try:
            console.print(f"\n[bold blue]Управление портфелем: {manager.current_portfolio.name}[/bold blue]")
            console.print("[cyan]1.[/cyan] Просмотр портфеля с информацией о стоимости")
            console.print("[cyan]2.[/cyan] Добавить актив")
            console.print("[cyan]3.[/cyan] Обновить актив")
            console.print("[cyan]4.[/cyan] Удалить актив")
            console.print("[cyan]5.[/cyan] Просмотр всех доступных активов (биржа)")
            console.print("[cyan]6.[/cyan] Просмотр детальной информации по активу (Биржа)")
            console.print("[cyan]7.[/cyan] Обновить курсы обмена с Binance")
            console.print("[cyan]8.[/cyan] Просмотр всех курсов обмена")
            console.print("[cyan]9.[/cyan] Редактировать список названий активов")
            console.print("[cyan]10.[/cyan] Визуализировать историю изменения цены для символа")
            console.print("[cyan]11.[/cyan] Сменить портфель")
            console.print("[cyan]12.[/cyan] Выход")
            choice = input("Выберите опцию: ").strip()
            if choice == "1":
                view_portfolio(manager)
            elif choice == "2":
                add_asset(manager)
            elif choice == "3":
                update_asset(manager)
            elif choice == "4":
                remove_asset(manager)
            elif choice == "5":
                view_all_exchange_assets()
            elif choice == "6":
                view_asset_details()
            elif choice == "7":
                update_all_fiat_rates_from_binance()
            elif choice == "8":
                view_exchange_rates()
            elif choice == "9":
                edit_asset_names()
            elif choice == "10":
                symbol = input("Введите символ актива для визуализации: ").strip().upper()
                plot_symbol_history(symbol)
            elif choice == "11":
                manager.select_portfolio()
            elif choice == "12":
                console.print("[bold green]Выход из управления портфелем.[/bold green]")
                break
            else:
                console.print("[red]Неверный выбор. Попробуйте снова.[/red]")
        except KeyboardInterrupt:
            console.print("\n[bold red]Программа прервана пользователем. Выход...[/bold red]")
            break


def main():
    manager = PortfolioManager()
    manager.select_portfolio()  # Выбор портфеля при запуске

    symbol = 'BTCUSDT'
    interval = '1h'
    fetch_and_store_klines(symbol, interval, limit=100)
    analysis = analyze_klines(symbol)
    if analysis:
        console.print("[bold blue]Результаты анализа:[/bold blue]")
        display_analysis(analysis)
        export_analysis(analysis, 'analysis_report.csv')

    interactive_portfolio_management(manager)
    manager.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Программа прервана пользователем. Выход...[/bold red]")