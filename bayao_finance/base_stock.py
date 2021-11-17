from bayao_finance.indicators import *


class BaseStock:

    def __init__(self, stock_token=None):
        if not stock_token:
            stock_token = 'Unknown'
        self.stock_token = stock_token

    def get_sma(self, data=None, n=20, min_periods=None, **kwargs):
        """
        Get a Series or DataFrame of Exponential Moving Average

        Parameters
        ----------
        data: Series or Dataframe, default None
            if None it is used self.
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
        if data is None:
            data = self
        return get_sma_from_data(data, n, min_periods, **kwargs)

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

    def get_macd(self, n_short=12, n_long=26, n_signal=9):
        """
        Generates a Moving Average Convergence Divergence

        Parameters
        ----------
        n_short: int
            Exponential Moving Average "n" for short-term EMA
        n_long: int
            Exponential Moving Average "n" for long-term EMA
        n_signal: int
            Exponential Moving Average "n" for signal EMA

        Returns
        -------
        DataFrame with index and index_signal for StockSeries ticker or StockFrame Columns
        """
        return get_macd_from_data(self, n_short=n_short, n_long=n_long, n_signal=n_signal, token=self.stock_token)

    def get_bollinger_bands(self, n=20, k=2):
        """
        Creates Dataframe with SMA and Bollinger Bands
        Parameters
        ----------
        n: int
            SMA span.
        k: int
            Multiplier to expand band linearly. It is multiplied by the standard deviation.

        Returns
        -------
        Dataframe with bb_inf (SMA - k * std), bb (SMA), bb_sup (SMA + k * std)

        """
        return get_bollinger_bands_from_data(self, n, k, token=self.stock_token)

    def get_rsi(self, n=14, min_periods=None, **kwargs):
        return get_rsi(self, n, min_periods, **kwargs)

    def get_returns(self):
        return get_returns_from_data(self)
