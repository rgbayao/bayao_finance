from datetime import date
import pandas as pd
import yfinance as yf
import numpy as np
import os


class CloseIndex:
    """
    Class to generate indexes with close or adj_close

    Available methods
    -----------------
        HistoricalData : atr

        CloseData : sma, ema, macd, borllinger bands, rsi

    Parameters
    ----------
    data : DataFrame
        One column = close or adj_close
        # todo : make it using string reading
    """
    def __init__(self, data):
        # Data must be a DataFrame wtih index of Timestamp or Datetime
        if data.index[0] > data.index[1]:
            data = data[::-1]
        self.close = data
        self.indexes = {"sma": self.get_sma,
                        "ema": self.get_ema,
                        "macd": self.get_macd,
                        "bb": self.get_bollinger_bands,
                        "rsi": self.get_rsi,
                        "returns": self.get_returns}

    def __repr__(self):
        return repr(self.close)

    def get_sma(self, data=None, n=20):
        # If data == None -> data = self.close

        if data is None:
            data = self.close

        return data.rolling(n).mean()

    def get_ema(self, data=None, n=20, min_periods=None):
        # min_periods for not placing nan, if none min_periods = n
        # If data == None -> data = self.close

        if data is None:
            data = self.close

        if not min_periods:
            min_periods = n

        return data.ewm(span=n, min_periods=min_periods).mean()

    def get_macd(self, data=None):
        # return a tuple: (MACD, signal)
        # If data == None -> data = self.close

        if data is None:
            data = self.close

        macd_calculation = self.get_ema(data=data, n=12).sub(self.get_ema(data=data, n=26))
        signal = macd_calculation.ewm(span=9, min_periods=9).mean()

        for i in data.columns:
            macd_calculation[i + '_signal'] = signal[i]

        columns_index = []
        for i in data.columns:
            columns_index.append(i)
            columns_index.append(i + '_signal')

        return macd_calculation[columns_index]

    def get_bollinger_bands(self, data=None, n=20, k=2):
        # return a tuple: (min, center, max)
        # If data == None -> data = self.close

        if data is None:
            data = self.close

        bb = self.get_sma(data=data, n=n)
        std = data.rolling(n).std()

        bb_inf = bb.sub(std.mul(k))
        bb_sup = bb.add(std.mul(k))

        return bb_inf, bb, bb_sup

    def get_rsi(self, data=None, n=14, com=None):
        if data is None:
            data = self.close
        if com is None:
            com = n - 1

        lost_index = data.index[:n]
        delta = data.diff().dropna().copy()
        u = delta * 0
        d = u.copy()
        u[delta > 0] = delta[delta > 0]
        d[delta < 0] = -delta[delta < 0]
        u[u.index[n - 1]] = np.mean(u[:n])  # first value is average of gains
        u = u.drop(u.index[:(n - 1)])
        d[d.index[n - 1]] = np.mean(d[:n])  # first value is average of losses
        d = d.drop(d.index[:(n - 1)])
        rs = u.ewm(com=n, min_periods=n).mean() / d.ewm(com=n, min_periods=n).mean()
        rsi_calc = 100 - 100 / (1 + rs)
        return rsi_calc.reindex(list(lost_index) + list(rsi_calc.index))

    def get_returns(self, data=None):
        if data is None:
            data = self.close
        return data.pct_change()


class HistoricalIndex(CloseIndex):
    """
    Class to generate indexes with ohlcav and store data

    Available methods
    -----------------
        HistoricalData : atr

        CloseData : sma, ema, macd, borllinger bands, rsi

    Parameters
    ----------
    data : DataFrame
        Columns should according to kind
    kind : string, default "ohlcav"
        Will define the columns names
        # todo : make it using string reading
    """

    def __init__(self, data, kind="ohlcav"):
        # DataFrame or list of DataFrames
        # Columns: [open, high, low, close, volume]
        # tickers: list or array
        self.kind = kind
        self.data = data.copy()

        if self.kind == "ohlcav":
            self.data = self.data.iloc[:, :6].copy()
            self.data.columns = ['open', 'high', 'low', 'close', 'adj_close', 'volume']
            self._has_atr = True
        else:
            raise AttributeError("only ohlcav available")

        if self.data.index[0] > self.data.index[1]:
            self.data = self.data[::-1]

        super().__init__(self.data.adj_close)
        self.indexes["atr"] = self.get_atr

    def get_atr(self, data=None, n=14):

        if not self._has_atr:
            return None

        if data is None:
            data = self.data

        tr = pd.DataFrame()
        tr['HL'] = data.high - data.low
        tr['CL'] = data.close.shift() - data.low
        tr['HC'] = data.high - data.close.shift()
        tr['max'] = tr.max(axis=1)
        atr_calculation = self.get_sma(data=tr['max'], n=n)

        return atr_calculation


class StockData(HistoricalIndex):
    """
    Manage data by downloading or loading ticker, it automatic saves a copy in the folder.
    Makes possible to get indexes from data.

    Parameters
    ----------
    ticker : string
        Make it according to the APIs
    name : string
        Just the name
    download : boolean, default True
        If False it will need to be loaded
        #todo: make it possible to load or download after init
    source : string, default yahoo
        Define the API provider
        #todo: implement pdr_reader and alpha_vantage
    """

    def __init__(self, ticker, name="", download=False, source="yahoo", **kwargs):

        self.tag = ticker
        if name == "":
            self.name = ticker

        # check if source is available
        if source not in ["yahoo"]:
            raise AttributeError("This source is not yet available")
        self.source = source

        # kind of columns format
        self.kind = ""

        data = None
        if download:
            data = self.download_data()
        elif "date" in kwargs:
            data = self.read_data(download_date=kwargs.get("date"))
        else:
            data = self.read_data()

        # init HistoricalIndex
        super().__init__(data, self.kind)

    def download_data(self):

        # download and prepare data
        if self.source == "yahoo":
            data = yf.download(self.tag)
            self.kind = "ohlcav"
            self._format_data_columns(data)
        else:
            raise AttributeError("This source is not yet available")

        try:
            os.mkdir(date.today().strftime("%Y-%m-%d"))
        except FileExistsError:
            pass
        # save data so you can download it later
        today = date.today().strftime("%Y-%m-%d")
        try:
            os.mkdir(today)
        except FileExistsError:
            pass
        data.to_csv(".\\" + today + "\\" + self.tag + "_" + self.source + "_" + today + ".csv")

        return data

    def read_data(self, download_date=None):
        # todo: make it work

        if download_date is None:
            download_date = date.today().strftime("%Y-%m-%d")
        else:
            pass

        if not os.path.isdir(download_date):
            raise IsADirectoryError("No such directory: " + download_date)

        if self.source == "yahoo":
            for i in os.listdir(".\\" + download_date):
                if i.startswith(self.tag):
                    filepath = ".\\" + download_date + "\\" + i
                    break
            else:
                raise FileNotFoundError("No file for " + self.tag + "stock")
            data = pd.read_csv(filepath, index_col=0, parse_dates=True)
            print(self.tag + " successfully read")
            self.kind = "ohlcav"
            self._format_data_columns(data)
        else:
            raise ValueError("Only yahoo source for now")
        return data

    def _format_data_columns(self, data):
        # todo: implement other "kinds"
        if data.index[0] > data.index[1]:
            data = data[::-1]
        if self.kind == "ohlcav":
            data.columns = ['open', 'high', 'low', 'close', 'adj_close', 'volume']
