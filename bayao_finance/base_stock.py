from bayao_finance.indicators import *


class BaseStock:

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
        return get_rsi(self, n, min_periods, **kwargs)

    def get_returns(self):
        return get_returns_from_data(self)
