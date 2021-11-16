from datetime import date
import pandas as pd
import yfinance as yf
import os
from bayao_finance import StockFrame


class StockData(StockFrame):
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
