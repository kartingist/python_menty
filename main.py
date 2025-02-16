import requests
import json

BASE_URL = "https://api.binance.com"

def fetch_binance_exchange_info():
    endpoint = "/api/v3/exchangeInfo"
    url = BASE_URL + endpoint
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Binance API: {e}")
        return None

def parse_exchange_info(data):
    currency_pairs_info = []
    if "symbols" in data:
        for symbol_data in data["symbols"]:
            pair_info = {
                "symbol": symbol_data["symbol"],
                "base_asset": symbol_data["baseAsset"],
                "quote_asset": symbol_data["quoteAsset"],
                "status": symbol_data["status"],
                "order_types": symbol_data["orderTypes"],
                "filters": symbol_data["filters"]
            }
            currency_pairs_info.append(pair_info)
    return currency_pairs_info

def main():
    exchange_data = fetch_binance_exchange_info()
    if exchange_data:
        currency_pairs_info = parse_exchange_info(exchange_data)
        if currency_pairs_info:
            print("Список валютных пар и подробная информация:")
            for pair_info in currency_pairs_info:
                print("-" * 30)
                print(f"Символ: {pair_info['symbol']}")
                print(f"Базовая валюта: {pair_info['base_asset']}")
                print(f"Котируемая валюта: {pair_info['quote_asset']}")
                print(f"Статус: {pair_info['status']}")
                print(f"Типы ордеров: {pair_info['order_types']}")
                print("Фильтры:")
                for filter_item in pair_info['filters']:
                    print(f"  - Тип фильтра: {filter_item['filterType']}")
                    for k, v in filter_item.items():
                        if k != 'filterType':
                            print(f"    - {k}: {v}")


if __name__ == "__main__":
    main()