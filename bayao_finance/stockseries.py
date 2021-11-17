import pandas as pd
from pandas import Series
from bayao_finance.indicators import *
from bayao_finance.base_stock import BaseStock
import numpy as np


class StockSeries(Series, BaseStock):
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

        BaseStock.__init__(self, stock_token=stock_token)
        Series.__init__(self, data, *args, **kwargs)

        self._stock_indexes = {"sma": self.get_sma,
                               "ema": self.get_ema,
                               "macd": self.get_macd,
                               "bb": self.get_bollinger_bands,
                               "rsi": self.get_rsi,
                               "returns": self.get_returns}

    @property
    def _constructor(self):
        return StockSeries

    @property
    def _constructor_expanddim(self):
        from bayao_finance import StockFrame
        return StockFrame


    def get_stock_indexes(self):
        return self._stock_indexes
