import aiohttp
import asyncio
import platform
import sys
import json
from datetime import datetime, timedelta


class HttpError(Exception):
    pass


class PrivatBankAPI:
    BASE_URL = 'https://api.privatbank.ua/p24api/exchange_rates'

    async def request(self, url: str):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result
                    else:
                        raise HttpError(f"Error status: {resp.status} for {url}")
            except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
                raise HttpError(f'Connection error: {url}', str(err))

    async def get_exchange_rates(self, date: str):
        try:
            response = await self.request(f'{self.BASE_URL}?date={date}')
            return response
        except HttpError as err:
            print(err)


class ExchangeRateFetcher:
    async def fetch_last_n_days(self, n_days: int):
        exchange_rates = []
        pb_api = PrivatBankAPI()
        current_date = datetime.now()

        n_days = min(n_days, 10)

        for i in range(n_days):
            shift_date = current_date - timedelta(days=i)
            shift_date_str = shift_date.strftime('%d.%m.%Y')
            exchange_rates.append(pb_api.get_exchange_rates(shift_date_str))

        return await asyncio.gather(*exchange_rates)


def filter_exchange_rates(response):
    filtered_data = []

    for day_data in response:
        day_rates = {}

        for rate in day_data['exchangeRate']:
            if rate['currency'] in ['EUR', 'USD']:
                currency = rate['currency']
                day_rates[currency] = {
                    'sale': rate.get('saleRate', rate['saleRateNB']),
                    'purchase': rate.get('purchaseRate', rate['purchaseRateNB'])
                }

        if day_rates:
            filtered_data.append({day_data['date']: day_rates})

    return filtered_data


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    if len(sys.argv) != 2:
        print("Usage: py .\main.py <days_to_fetch>")
        sys.exit(1)

    try:
        days_to_fetch = int(sys.argv[1])
    except ValueError:
        print("Error: days_to_fetch must be an integer")
        sys.exit(1)

    fetcher = ExchangeRateFetcher()
    result = asyncio.run(fetcher.fetch_last_n_days(days_to_fetch))
    filtered_result = filter_exchange_rates(result)

    print(json.dumps(filtered_result, indent=2))
