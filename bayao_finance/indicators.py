from pandas import Series


def get_sma_from_data(data: Series, n=20, min_periods=None, **kwargs):
    if not min_periods:
        min_periods = n
    return data.rolling(n, min_periods=min_periods, **kwargs).mean()


def get_ema_from_data(data, n=20, min_periods=None, **kwargs):
    if not min_periods:
        min_periods = n
    return data.ewm(span=n, min_periods=min_periods, **kwargs).mean()


def get_macd_from_data(data, token=None):
    # return a tuple: (MACD, signal)
    # If data == None -> data = self.close

    macd_calculation = (
        get_ema_from_data(data=data, n=12)
            .sub(get_ema_from_data(data=data, n=26))
    )

    signal = macd_calculation.ewm(span=9, min_periods=9).mean()

    if isinstance(macd_calculation, Series):
        if not token:
            token = 'macd'
        macd_calculation.to_frame(name=token)

    for i in data.columns:
        macd_calculation[i + '_signal'] = signal[i]

    columns_index = []
    for i in data.columns:
        columns_index.append(i)
        columns_index.append(i + '_signal')

    return macd_calculation[columns_index]


def get_bollinger_bands_from_data(data, n=20, k=2):
    # return a tuple: (min, center, max)
    # If data == None -> data = self.close

    bb = get_sma_from_data(data, n=n)
    std = data.rolling(n).std()

    bb_inf = bb.sub(std.mul(k))
    bb_sup = bb.add(std.mul(k))

    return bb_inf, bb, bb_sup


def get_returns_from_data(data):
    return data.pct_change()
