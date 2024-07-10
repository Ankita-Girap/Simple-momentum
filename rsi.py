from fyers_api import fyersModel
import pandas as pd
import pandas_ta as ta
import pytz

IST = pytz.timezone('Asia/Kolkata')

client_id = '9M8CLGBRH0-657'
# generate access token
access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc4h0n9JhcGkuZnllcnMuaW4iLCJpYXQiOjG6MDczNzAwOTgsImV4cCI6MTcwNzQzODYxOCwibmJmIjoxNzA3MzcwMDk4LCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6ImFjY2Vzc190b2tlbiIsImF0X2hhc2giOiJnQUFBQUFCbHhHWnl2VEFuaV9UZ2RSTUtKMThlbDd2WEZ3QTByUldZWWVsRUVDYmhUOTBZYmNnOGVvSFNIcnNvTmptVkxOV0N1ZzRYcVpxcmR0RHZhNjhRZDR4U0Iyeko2WDh3dm5YREdoYzIyek9NbFBlRlRhWT0iLCJkaXNwbGF5X25hbWUiOiJZQVNIIFZJTUFMIFRIQUtVUiIsIm9tcyI6IksxIiwiaHNtX2tleSI6ImFkODVhMjI2OTRlMmE4NWU4NjUxYTUyZDdhMWQ3NTJiNTUwNjA2NjIxNTkxYjUyMjliMzMxNWZmIiwiZnlfaWQiOiJZWTAwNTA0IiwiYXBwVHlwZSI6MTAwLCJwb2FfZmxhZyI6Ik4ifQ.WcRJxdCy2ADgkHgJJaWjuMqRUNMKES8TfvQ6yoDr4Zs'
fyers_obj = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="fyers-logs/")
banknifty_symbol = "NSE:BANKNIFTY24FEBFUT"
flag = False

long_option = {'bought': False, 'buying-price': 0, 'selling-price': 0, 'sl': ''}
short_option = {'bought': False, 'buying-price': 0, 'selling-price': 0, 'sl': ''}

quantity = 1


def place_order(instrument, side):
    data = {
        "symbol": instrument,
        "qty": quantity,
        "type": 2,
        "side": side,
        "productType": "MARGIN",
        "limitPrice": 0,
        "stopPrice": 0,
        "validity": "DAY",
        "disclosedQty": 0,
        "offlineOrder": False,
        "stopLoss": 0,
        "takeProfit": 0
    }
    return fyers_obj.place_order(data)


def calculate_rsi(df):
    try:
        rsi = ta.rsi(df['close'])
        df['rsi'] = rsi
        rsi_val = rsi[-1]
        print("rsi val", rsi_val)
        pd.DataFrame(df).to_csv("all_values.csv")
        return rsi_val
    except ValueError:
        print(1, ValueError)


def long_position(rsi, val):
    status, price = '', ''

    if rsi >= 60 and long_option['bought'] is False:
        closest_strike = int(round((val / 100), 0) * 100)
        bid_price = closest_strike - 200
        instrument = f"NSE:BANKNIFTY24214{bid_price}CE"
        # order_id = place_order(instrument, 1)
        long_option['bought'] = True
        long_option['buying-price'] = bid_price
        long_option['sl'] = long_option['buying-price'] - 35
        status, price = "buy", bid_price

    if long_option['bought'] is True and (val <= long_option['sl'] or int(rsi) <= 50):
        instrument = f"NSE:BANKNIFTY24214{val}PE"
        # order_id = place_order(instrument, -1)
        long_option['selling-price'] = val
        long_option['bought'] = False
        long_option['sl'] = ''
        status, price = "exit", val

    if long_option['bought'] is True and val > long_option['buying-price'] + 35 and status == '':
        long_option['sl'] = long_option['sl'] + (val - (long_option['buying-price'] + 35))

    return status, price


def short_position(rsi, val):
    status, price = '', ''

    if rsi <= 40 and short_option['bought'] is False:
        closest_strike = int(round((val / 100), 0) * 100)
        bid_price = closest_strike - 200
        instrument = f"NSE:BANKNIFTY24214{bid_price}CE"
        # order_id = place_order(instrument, 1)
        short_option['buying-price'] = bid_price
        short_option['bought'] = True
        short_option['sl'] = short_option['buying-price'] - 35
        status, price = 'buy', bid_price
    if short_option['bought'] is True and (val <= short_option['sl'] or int(rsi) >= 50):
        short_option['bought'] = False
        short_option['selling-price'] = val
        instrument = f"NSE:BANKNIFTY24214{val}PE"
        # order_id = place_order(instrument, -1)
        short_option['sl'] = ''
        status, price = 'exit', val

    if short_option['bought'] is True and val > short_option['buying-price'] + 35  and status == '':
        short_option['sl'] = short_option['sl'] + (val - (short_option['buying-price']+35))

    return status, price


def get_candle_details():
    try:
        global flag
        symbolData = {
            "symbol": 'NSE:BANKNIFTY24FEBFUT',
            "resolution": "1",
            "date_format": "1",
            "range_from": "2024-02-08",
            "range_to": "2024-02-09",
            "cont_flag": "1"
        }
        data = fyers_obj.history(symbolData)
        df = pd.DataFrame(data['candles'])
        df.to_csv('candles_details_raw.csv')
        cols = ["datetime", 'open', 'high', 'low', 'close', 'volume']
        df.columns = cols
        df["datetime"] = pd.to_datetime(df["datetime"], unit='s')
        df["datetime"] = df["datetime"].dt.tz_localize('utc').dt.tz_convert('Asia/Kolkata')
        df["datetime"] = df["datetime"].dt.tz_localize(None)
        df.set_index('datetime', inplace=True)
        df.to_csv('candles_details_array_1.csv')
        rsi = calculate_rsi(df)
        # Need to check which position should be called.
        # long_position(rsi)
        # short_position(rsi)
        print('ended')
        flag = True
    except ValueError:
        print(ValueError)


# get_candle_details()

def calculationOnCsv():
    try:
        data = pd.read_csv('all_values.csv')
        for i, rec in data.iterrows():
            rsi = rec['rsi']
            close_val = rec['close']
            if rsi is not None:
                long_status, long_price = long_position(rsi, close_val)
                data.at[i, 'long_position'] = long_status
                data.at[i, 'long_order_price'] = long_price
                data.at[i, 'stop loss long pos'] = long_option['sl']
                data.at[i, 'Long profit/loss'] = long_option['selling-price'] - long_option['buying-price'] if long_status == 'exit' else ''

                short_status, short_price = short_position(rsi, close_val)
                data.at[i, 'short_position'] = short_status
                data.at[i, 'short_order_price'] = short_price
                data.at[i, 'stop loss short pos'] = short_option['sl']
                data.at[i, 'Short profit/loss'] = short_option['selling-price'] - short_option['buying-price'] if short_status == 'exit' else ''

                if rec['datetime'].find('15:29') > -1:
                    if long_option['bought']:
                        data.at[i, 'Long profit/loss'] = close_val - long_option['buying-price']

                    if short_option['bought']:
                        data.at[i, 'Short profit/loss'] = close_val - short_option['buying-price']
        data.to_csv("final_csv.csv")
    except ValueError:
        print(ValueError)


calculationOnCsv()
