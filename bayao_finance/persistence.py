import datetime
import pandas as pd
import yfinance as yf
import os
from bayao_finance import StockFrame


def _clean_date(d):
    if d is None:
        save_date = datetime.date.today()
    elif isinstance(d, str):
        save_date = datetime.datetime.strptime(d, "%Y-%m-%d")
    elif isinstance(d, datetime.date):
        save_date = d
    else:
        raise AttributeError('file_date must be a datetime object, a string in "%Y-%m-%d" format or "now"')
    return save_date


class StockManipulator:
    """
    Manage data by downloading or loading ticker, it automatic saves a copy in folder.
    Automatic returns in StockFrame so it can use indicators.

    Parameters
    ----------
    source : string, default yahoo
        Define the API provider
        #todo: implement pdr_reader and alpha_vantage
    """

    def __init__(self, source="yahoo"):

        # check whether source is available
        if source not in ["yahoo"]:
            raise AttributeError("This source is not yet available")
        self.source = source
        self.data_list = []
        self.data_dict = {}
        self.tickers = []

    def download_data(self, tickers, save_data=False, period="max", interval='1d', start=None, end=None,
                      **kwargs):
        """
        Parameters
        ----------
        save_data : bool
            Default True. If false won't save the data in computer
        tickers : str, list
            List of tickers to download
        period : str
            Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            Either Use period parameter or use start and end
        interval : str
            Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
            Default is 1d
            Intraday data cannot extend last 60 days
        start: str
            Download start date string (YYYY-MM-DD) or _datetime.
            Default is 1900-01-01
        end: str
            Download end date string (YYYY-MM-DD) or _datetime.
            Default is now
        kwargs:
            Other values from API provider

        Returns
        -------
        dict
            keys = tickers, values = StockFrame
        """

        if isinstance(tickers, str):
            self.tickers = [tickers]
        else:
            self.tickers = tickers

        if self.source == "yahoo":
            self._download_from_yfinance(tickers, period=period, interval=interval, start=start, end=end, **kwargs)
        else:
            raise AttributeError("This source is not yet available")

        if save_data:
            self._save_data(end)

        self.data_dict = dict(zip(self.tickers, self.data_list))
        return self.data_dict

    def read_data(self, file_date=None):
        """

        Parameters
        ----------
        file_date: str
            Files download date string (YYYY-MM-DD) or _datetime.
            Default is 'now'

        Returns
        -------
        dict
            keys = tickers, values = StockFrame
        """

        read_date = _clean_date(file_date)

        date_string = read_date.strftime("%Y-%m-%d")
        folder_path = os.path.join('.', 'data', date_string)

        if not os.path.isdir(folder_path):
            raise IsADirectoryError("No such directory: " + folder_path)

        self._read_data(folder_path, date_string)

        return self.data_dict

    def _read_data(self, folder_path, date_prefix):
        folder_tickers_with_extension = [i.split('_')[-1] for i in os.listdir(folder_path)]
        folder_tickers = [i.split('.')[0] for i in folder_tickers_with_extension]

        self.data_list = []
        self.data_dict = {}
        for i in self.tickers:
            if i not in folder_tickers:
                raise FileNotFoundError(f'No file for ticker {i} in {folder_path}')
            else:
                file_path = os.path.join(folder_path, f'{date_prefix}_{i}')
                df = StockFrame(pd.read_csv(file_path), index_col=0, parse_dates=True, stock_token=i)
                self.data_dict[i] = df
                self.data_list.append(df)

    def _segregate_yahoo_data(self, data, tickers):
        self.data_list = []
        for i in tickers:
            self.data_list.append(StockFrame(data[i], stock_token=i))

    def _download_from_yfinance(self, tickers, **kwargs):
        self.data_list = []
        self.data_dict = {}
        data = yf.download(tickers, group_by='ticker', **kwargs)
        if isinstance(tickers, list):
            self._segregate_yahoo_data(data, tickers)
        else:
            self.data_list = [data]

    def _save_data(self, last_date='now'):

        save_date = _clean_date(last_date)

        # save data so you can download it later
        today = save_date.strftime("%Y-%m-%d")

        save_path = os.path.join('.', 'data', today)
        os.makedirs(save_path, exist_ok=True)

        for i in range(0, len(self.tickers)):
            self.data_list[i].to_csv(os.path.join(save_path, f'{today}_{self.tickers[i]}'))

