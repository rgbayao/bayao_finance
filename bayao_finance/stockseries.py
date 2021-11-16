from pandas import Series
from bayao_finance.indicators import *
import numpy as np


class StockSeries(Series):
    """
    Series which can generate indexes with close or adj_close

    Parameters
    ----------
    data : Series
        One column = close or adj_close
    """

    _metadata = ["_stock_indexes", "_close_indexes", "stock_token"]

    def __init__(self, data, *args, stock_token=None, **kwargs):

        # Data must be a DataFrame wtih index of Timestamp or Datetime
        if isinstance(data, Series):
            if data.index[0] > data.index[1]:
                data = data[::-1]
        elif isinstance(data, np.ndarray):
            try:
                if kwargs.get('index')[0] > kwargs.get('index')[1]:
                    data = data[::-1]
                    kwargs['index'] = kwargs['index'][::-1]
            except IndexError:
                pass

        super().__init__(data, *args, **kwargs)

        self.name = 'close'

        self._stock_indexes = {"sma": self.get_sma,
                               "ema": self.get_ema,
                               "macd": self.get_macd,
                               "bb": self.get_bollinger_bands,
                               "rsi": self.get_rsi,
                               "returns": self.get_returns}
        if not stock_token:
            stock_token = 'Unknown'
        self.stock_token = stock_token

    @property
    def _constructor(self):
        return StockSeries

    @property
    def _constructor_expanddim(self):
        from bayao_finance import StockFrame
        return StockFrame

    def get_sma(self, n=20, min_periods=None, **kwargs):
        """
        Get a Series or DataFrame of Exponential Moving Average

        Parameters
        ----------
        n:int = Number of rows for index.
        min_periods: int, default None
            Minimum number of observations in window required to have a value
            (otherwise result is NA). For a window that is specified by an
            offset, min_periods will default to 1.
            Otherwise, min_periods will default to the size of the window.


        Returns
        -------
        Series
            The moving average of the close index

        Other Parameters
        ----------------
        **kwargs: pandas.Series().rolling properties

        """
        return get_sma_from_data(self, n, min_periods, **kwargs)

    def get_ema(self, n=20, min_periods=None, **kwargs):
        """
        Get a Series of Exponential Moving Average

        Parameters
        ----------
        n:int = Number of rows for index.
        min_periods: int, default None
            Minimum number of observations in window required to have a value
            (otherwise result is NA). For a window that is specified by an
            offset, min_periods will default to 1.
            Otherwise, min_periods will default to the size of the window.


        Returns
        -------
        Series
            The moving average of the close index

        Other Parameters
        ----------------
        **kwargs: pandas.Series().rolling properties

        """
        return get_ema_from_data(self, n, min_periods, **kwargs)

    def get_macd(self):
        return get_macd_from_data(self, self.token)

    def get_bollinger_bands(self, n=20, k=2):
        return get_bollinger_bands_from_data(self, n, k)

    def get_rsi(self, n=14, min_periods=None, **kwargs):
        if not min_periods:
            min_periods = n
        data = self

        delta = data.diff().copy()
        u = np.where(delta >= 0, delta, 0)
        d = np.where(delta < 0, -1 * delta, 0)
        rs = (
                u.ewm(alpha=1 / n, min_periods=min_periods, **kwargs).mean() /
                d.ewm(alpha=1 / n, min_periods=min_periods, **kwargs).mean()
        )
        rsi_calc = 100 - 100 / (1 + rs)
        return rsi_calc

    def get_returns(self):
        return self.get_returns_from_data(self)

    def get_stock_indexes(self):
        return self._stock_indexes
