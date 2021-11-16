from bayao_finance.stockseries import StockSeries
from pandas import DataFrame, Series
import numpy as np
import pandas as pd
import re
from bayao_finance.decorators import singleton
from bayao_finance.base_stock import BaseStock


def no_leading_or_trailing_pattern(word, leading='(?<![a-zA-Z])', trailing='(?![a-zA-Z]|_)'):
    return f'{leading}{word}{trailing}'


OPEN_PATTERN = no_leading_or_trailing_pattern('open')
HIGH_PATTERN = no_leading_or_trailing_pattern('high')
LOW_PATTERN = no_leading_or_trailing_pattern('low')
CLOSE_PATTERN = no_leading_or_trailing_pattern('close',
                                               leading=r'((?<!(adj)(\s|_|-))(?<!(adjusted)(\s|_|-))(?<![a-zA-Z]))')
ADJ_CLOSE_PATTERN = no_leading_or_trailing_pattern(r'((?<=(adjusted)(\s|_|-))|(?<=(adj)(\s|_|-)))close',
                                                   leading='')
VOLUME_PATTERN = no_leading_or_trailing_pattern('volume')


@singleton
class ColPatternMapper:
    def __init__(self):
        flags = re.IGNORECASE
        self.compile_list = {'open': re.compile(OPEN_PATTERN, flags=flags),
                             'high': re.compile(HIGH_PATTERN, flags=flags),
                             'low': re.compile(LOW_PATTERN, flags=flags),
                             'close': re.compile(CLOSE_PATTERN, flags=flags),
                             'adj_close': re.compile(ADJ_CLOSE_PATTERN, flags=flags),
                             'volume': re.compile(VOLUME_PATTERN, flags=flags),
                             }
        self.mapper = {}
        self.founds_array = np.zeros(len(self.compile_list))

    def map_columns(self, columns):
        self.founds_array = np.zeros(len(self.compile_list))
        self.mapper = {}
        for i in columns:
            self._map_col(i)
        return self.mapper

    def _map_col(self, col):
        counter = 0
        for key, value in self.compile_list.items():
            if value.search(col):
                self.founds_array[counter] += 1
                self._mark_map(col, key, self.founds_array[counter])
            counter += 1

    def _mark_map(self, col, key, matches):
        if matches == 1:
            self.mapper[col] = key
        else:
            self.mapper[col] = f'{key}_{matches}'

    def get_kind(self):
        kind_mapper = ['o', 'h', 'l', 'c', 'a', 'v']
        kind = ''
        for i in range(0, len(self.founds_array)):
            if self.founds_array[i] > 0:
                kind += kind_mapper[i]
        return kind


def _ensure_columns(columns):
    cols_map = _get_cols_map(columns)
    cols_kind = _get_cols_kind()
    return cols_map, cols_kind


def _get_cols_map(columns):
    mapper = ColPatternMapper()
    col_map = mapper.map_columns(columns)
    return col_map


def _get_cols_kind():
    mapper = ColPatternMapper()
    kind = mapper.get_kind()
    return kind


class StockFrame(DataFrame, BaseStock):
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

        BaseStock.__init__(self, stock_token=stock_token)
        DataFrame.__init__(self, data, *args, **kwargs)

        if kind is None:
            cols_map, kind = _ensure_columns(list(self.columns))
        else:
            cols_map = _get_cols_map(list(self.columns))

        self._hist_kind = kind
        self.rename(columns=cols_map, inplace=True)

        if 'ohlc' in self._hist_kind or 'ohla' in self._hist_kind:
            self._has_atr = True

        if 'a' in self._hist_kind:
            self.close_col_name = 'adj_close'
        elif 'c' in self._hist_kind:
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
            result.__class__ = StockFrame
            result.close_col_name = None
        return result

    def __setattr__(self, attr, val):
        # have to special case geometry b/c pandas tries to use as column...
        if attr == "target_close":
            object.__setattr__(self, attr, val)
        else:
            super().__setattr__(attr, val)

    def _get_target_close(self):
        if self.close_col_name is None:
            return None
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
        elif isinstance(col, str):
            if col in frame.columns:
                frame.close_col_name = col

        if not inplace:
            return frame

    def get_atr(self, n=14):

        if not self._has_atr:
            return None

        tr_hl = self.high - self.low
        tr = tr_hl.to_frame(name='HL')

        tr['CL'] = self[self.close_col_name].shift() - self.low
        tr['HC'] = self.high - self.close.shift()
        tr['max'] = tr.max(axis=1)
        atr_calculation = self.get_sma(data=tr['max'], n=n)

        return atr_calculation
