from copy import deepcopy
import pandas as pd
import numpy as np


class TargetGenerator:
    """
    Class to generate Target Columns for the data analysis
    todo : make it static?

    Available Targets
    -----------------
        betOnMonday :
            Target only on mondays which the week had a profit above a defined value

    Parameters
    ----------

    """

    def __init__(self):
        self.stock_data = None
        self._parameters = {}
        self.target = []

    def _bet_on_monday(self, min_profit):
        data = self.stock_data.data
        target = []

        for i in range(0, len(data)):
            if data.index[i].dayofweek == 0:
                temp = 0
                current_day = -1
                j = i
                while data.index[j].dayofweek > current_day:
                    if (data.iloc[j]["high"] / data.iloc[i]["open"]) - 1 >= min_profit:
                        temp = 1
                        break
                    current_day = data.index[j].dayofweek
                    j += 1
                    if j >= len(data):
                        break
                target.append(temp)
            else:
                target.append(0)
        self.target = target


class InputFormatter(TargetGenerator):

    def __init__(self):
        super().__init__()
        self.data_inputs = None
        self.reference = []
        self.to_filter = ""

    def fit_transform(self, data, target, include_close=True, normalize=False, to_filter=True, **kwargs):
        self.stock_data = data
        self.data_inputs = pd.DataFrame()

        if target == "bom":
            if "min_profit" not in kwargs.keys():
                raise AttributeError("min_profit not defined")
            else:
                self._bet_on_monday(kwargs.get("min_profit"))
                self.to_filter = "monday"
        else:
            raise AttributeError("Target type yet not available")

        if include_close:
            self.data_inputs["close"] = self.stock_data.close

        if "indexes" in kwargs.keys():
            self._set_indexes(kwargs["indexes"])
        elif not include_close:
            raise ValueError("no inputs included")

        if normalize:
            if "how" in kwargs.keys():
                self.normalizer(how=kwargs.get("how"))
            else:
                self.normalizer()
        self.data_inputs["target"] = self.target

        if to_filter:
            self.filter_data()
        else:
            pass
        print(self.stock_data.tag + " inputs are ready for analysis")

        self._check_consistency()

        return self.data_inputs

    def _set_indexes(self, indexes):
        inputs = pd.DataFrame()
        self.reference = []
        for i in indexes.keys():
            if i not in self.stock_data.indexes.keys():
                raise AttributeError("Index " + i + " not available for data")
            else:
                temp = self._gen_index(i, indexes.get(i))
                for j in temp.columns:
                    inputs[j] = temp[j]
        for i in inputs.columns:
            self.data_inputs[i] = inputs[i]

    def _gen_index(self, index, parameters):
        if not isinstance(parameters, list):
            parameters = [parameters]
        temp = pd.DataFrame()
        for i in parameters:
            if index in ["sma", "ema", "rsi", "atr"]:
                temp[index + "_" + str(i)] = self.stock_data.indexes[index](n=i)
                self.reference.append(index)
            elif index == "bb":
                bollinger = self.stock_data.indexes[index](n=i)
                temp[index + "_inf_" + str(i)] = bollinger[0]
                temp[index + "_med_" + str(i)] = bollinger[1]
                temp[index + "_sup_" + str(i)] = bollinger[2]
                self.reference.append(index)
            else:
                raise AttributeError(i + 'yet to develop - try "sma", "ema", "rsi", "atr" or "bb"')
        return temp

    def normalizer(self, how="dayClose"):
        for i in range(0, len(self.reference)):
            if self.reference[i] in ["sma", "ema"]:
                self.data_inputs.iloc[:, i] = \
                    self.data_inputs.iloc[:, i] / self.stock_data.close
            elif self.reference[i] == "rsi":
                self.data_inputs.iloc[:, i] = self.data_inputs.iloc[:, i] / 100
            elif self.reference[i] == "bb":
                self.data_inputs.iloc[:, i] = (self.stock_data.close - self.data_inputs.iloc[:, i+1])\
                                      / (self.data_inputs.iloc[:, i+1] - self.data_inputs.iloc[:, i])
                self.data_inputs.drop(columns=self.data_inputs.columns[i+1:i+3], inplace=True)
                columns = list(self.data_inputs.columns)
                columns[i] = columns[i].replace("_inf", "")
                self.data_inputs.columns = columns
            else:
                continue

    def filter_data(self):
        if self.to_filter == "":
            raise ValueError("Please define a filter to self.filter")
        elif self.to_filter == "monday":
            self.data_inputs = self.data_inputs[self.data_inputs.index.dayofweek == 0]

    def _check_consistency(self):
        temp = self.data_inputs.copy()

        temp = temp.dropna().reset_index()

        if np.any(np.isinf(temp.iloc[:, 1:])):
            max_drop = 0
            for i in temp.columns[1:]:
                if np.any(np.isinf(temp[i])):
                    if temp[np.isinf(temp[i])].index[-1] + int(i.split("_")[1]) > max_drop:
                        max_drop = temp[np.isinf(temp[i])].index[-1] + int(i.split("_")[1])
                    temp = temp.drop(labels=range(temp.index[0], temp[np.isinf(temp[i])].index[-1] + 1))
            temp.drop(labels=range(temp.index[0], max_drop+1))

        self.data_inputs = temp.set_index("Date")

        return self.data_inputs

