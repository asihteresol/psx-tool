import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import pandas as pd

URL = "https://dps.psx.com.pk/market-watch"

def create_session():
    session = requests.Session()

    retry = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504]
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session

def get_psx_data():
    session = create_session()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    response = session.get(URL, headers=headers, timeout=30)

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    rows = table.find_all("tr")[1:]

    data = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 7:
            continue

        data.append({
            "symbol": cols[0].text.strip(),
            "sector": cols[1].text.strip(),
            "list_in": cols[2].text.strip(),
            "LDCP": cols[3].text.strip(),
            "open": cols[4].text.strip(),
            "high": cols[5].text.strip(),
            "low": cols[6].text.strip(),
            "current": cols[7].text.strip(),
            "change": cols[8].text.strip(),
            "change_percent": cols[9].text.strip(),
            "volume": cols[10].text.strip(),
            "signal": ""
        })

    return pd.DataFrame(data)


def generate_signal(change_percent):
    if change_percent > 2:
        return "BUY"
    elif change_percent < -2:
        return "SELL"
    else:
        return "HOLD"

def smart_signal(change_percent):
    # if change_percent > 3:
    #     return "STRONG BUY"
    if change_percent > 1.5:
        return "BUY"
    # elif change_percent < -3:
    #     return "STRONG SELL"
    elif change_percent < -1.5:
        return "SELL"
    else:
        return "HOLD"

# def add_signals(df):
#     df["change_percent"] = df["change_percent"].str.replace('%','').astype(float)
#     df["signal"] = df["change_percent"].apply(generate_signal)
#     return df

def add_signals(df):
    df["change_percent"] = df["change_percent"].str.replace('%','').astype(float)
    df["signal"] = df["change_percent"].apply(smart_signal)
    return df

def explain_signal(row):
    if row["signal"] == "BUY":
        return "Stock upward trend mein hai, buying pressure strong hai"
    elif row["signal"] == "SELL":
        return "Stock downward trend mein hai, selling pressure zyada hai"
    else:
        return "Market neutral hai, wait karna better hai"
    
def calculate_rsi(prices, period=14):
    prices = prices.astype(float)
    delta = prices.diff()

    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

def get_stock_history(symbol):
    url = f"https://dps.psx.com.pk/timeseries/eod/{symbol}"

    try:
        response = requests.get(url, timeout=30)
        data = response.json()

        if not data:
            return None

        df = pd.DataFrame(data)

        if "close" not in df.columns:
            return None

        df["close"] = df["close"].astype(float)

        if len(df) < 14:
            return None

        return df

    except Exception as e:
        print("Error:", e)
        return None

def add_rsi(df):
    df["rsi"] = calculate_rsi(df["close"])
    return df

def rsi_signal(rsi):
    if rsi < 30:
        return "BUY"
    elif rsi > 70:
        return "SELL"
    else:
        return "HOLD"