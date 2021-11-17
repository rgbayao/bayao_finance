from pandas import Series
from numpy import where


def get_sma_from_data(data, n=20, min_periods=None, **kwargs):
    if not min_periods:
        min_periods = n
    return data.rolling(n, min_periods=min_periods, **kwargs).mean()


def get_ema_from_data(data, n=20, min_periods=None, **kwargs):
    if not min_periods:
        min_periods = n
    return data.ewm(span=n, min_periods=min_periods, **kwargs).mean()


def get_macd_from_data(data, n_short=12, n_long=26, n_signal=9, token=None):
    # return a tuple: (MACD, signal)
    # If data == None -> data = self.close

    macd_calculation = (
        get_ema_from_data(data=data, n=n_short)
        .sub(get_ema_from_data(data=data, n=n_long))
    )

    signal = macd_calculation.ewm(span=n_signal, min_periods=n_signal).mean()

    if isinstance(macd_calculation, Series):
        if not token:
            token = 'macd'
        macd_calculation = macd_calculation.to_frame(name=token)
        signal = signal.to_frame(name=token)

    columns_index = []
    macd_cols = macd_calculation.columns
    for i in macd_cols:
        macd_calculation[i + '_signal'] = signal[i]
        columns_index.extend([i, f'{i}_signal'])

    return macd_calculation[columns_index]


def get_bollinger_bands_from_data(data, n=20, k=2, token=None):
    # return a tuple: (min, center, max)
    # If data == None -> data = self.close

    bb = get_sma_from_data(data, n=n)
    std = data.rolling(n).std()

    bb_inf = bb.sub(std.mul(k))
    bb_sup = bb.add(std.mul(k))

    if isinstance(bb, Series):
        if not token:
            token = 'bb'
        bb = data.to_frame(name=token)
        bb_inf = bb_inf.to_frame(name=token)
        bb_sup = bb_sup.to_frame(name=token)

    columns_index = []
    for i in bb.columns:
        bb[i + '_inf'] = bb_inf[i]
        bb[i + '_sup'] = bb_sup[i]
        columns_index.extend([f'{i}_inf', i, f'{i}_sup'])

    return bb[columns_index]


def get_rsi(data, n=14, min_periods=None, **kwargs):
    if not min_periods:
        min_periods = n

    delta = data.diff().copy()
    u = delta * 0
    d = delta * 0
    u[delta >= 0] = delta[delta >= 0]
    d[delta < 0] = delta[delta < 0]
    rs = (
            u.ewm(alpha=1 / n, min_periods=min_periods, **kwargs).mean() /
            d.ewm(alpha=1 / n, min_periods=min_periods, **kwargs).mean()
    )
    rsi_calc = 100 - 100 / (1 + rs)
    return rsi_calc


def get_returns_from_data(data):
    return data.pct_change()
