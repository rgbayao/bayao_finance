class TickerParser:
    def __init__(self, ticker, suffix=None):
        if '_' in ticker:
            ticker = ticker.replace('_', '.')
        if suffix and '.' not in ticker:
            ticker = f'{ticker}.{suffix}'
        self.ticker = ticker

    @property
    def ticker(self):
        return self._ticker

    @ticker.setter
    def ticker(self, value):
        if '.' in value:
            parts = value.split('.')
            self.ticker_name = parts[0]
            self.market_suffix = parts[1]
        self._ticker = value

    def save_format(self):
        return self.ticker.replace('.', '_')


