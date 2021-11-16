from bayao_finance.stockseries import StockSeries
from pandas import DataFrame, Series
import numpy as np
import pandas as pd


class StockFrame(DataFrame):
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

    _metadata = ["_stock_indexes", "close_col_name", "_hist_kind", "stock_token"]

    def __init__(self, data, *args, stock_token=None, kind=None, **kwargs):
        # DataFrame or list of DataFrames
        # Columns: [open, high, low, close, volume]
        # tickers: list or array

        if isinstance(data, DataFrame):
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

        if not stock_token:
            stock_token = 'Unknown'
        self.stock_token = stock_token

        self._hist_kind = kind

        if self._hist_kind == "ohlcav":
            self.columns = pd.Index(['open', 'high', 'low', 'close', 'adj_close', 'volume'])
            self.close_col_name = 'adj_close'
            self._has_atr = True
        elif self._hist_kind == "ohlcv":
            self.columns = pd.Index(['open', 'high', 'low', 'close', 'volume'])
            self._has_atr = True
            self.close_col_name = 'close'
        elif self._hist_kind == 'c':
            self.columns = pd.Index(['target_close'])
            self._has_atr = False
            self.close_col_name = 'target_close'
        else:
            self._has_atr = False
            self.columns = pd.Index([i.lower() for i in self.columns])
            if 'target_close' in self.columns:
                self.close_col_name = 'target_close'
            elif 'adj_close' in self.columns:
                self.close_col_name = 'adj_close'
            elif 'close' in self.columns:
                self.close_col_name = 'close'
            else:
                self.close_col_name = None

    @property
    def _constructor(self):
        return StockFrame

    @property
    def _constructor_sliced(self):
        return StockSeries

    def __getitem__(self, key):
        """
        If the result is a column containing only 'geometry', return a
        GeoSeries. If it's a DataFrame with a 'geometry' column, return a
        GeoDataFrame.
        """
        result = super().__getitem__(key)
        close_col = self.close_col_name
        if isinstance(result, DataFrame) and close_col in result:
            result.__class__ = StockFrame
            result.close_col_name = close_col
        elif isinstance(result, DataFrame) and close_col not in result:
            result.__class__ = DataFrame
        return result

    def __setattr__(self, attr, val):
        # have to special case geometry b/c pandas tries to use as column...
        if attr == "target_close":
            object.__setattr__(self, attr, val)
        else:
            super().__setattr__(attr, val)

    def _get_target_close(self):
        return self[self.close_col_name]

    def _set_target_close(self, col):
        self.set_close(col, inplace=True)

    target_close = property(
        fget=_get_target_close, fset=_set_target_close, doc="CloseIndex for HistoricalData"
    )

    def set_close(self, col, inplace=False):
        if inplace:
            frame = self
        else:
            frame = self.copy()

        if isinstance(col, Series):
            frame.close_col_name = col.name
            frame[frame.close_col_name] = col

        if not inplace:
            return frame

    # def get_atr(self, n=14):
    #
    #     if not self._has_atr:
    #         return None
    #
    #     tr = pd.DataFrame()
    #     tr['HL'] = self.high - self.low
    #     tr['CL'] = self[self.close_col_name].shift() - self.low
    #     tr['HC'] = self.high - self.close.shift()
    #     tr['max'] = tr.max(axis=1)
    #     atr_calculation = self.get_sma(data=tr['max'], n=n)
    #
    #     return atr_calculation
