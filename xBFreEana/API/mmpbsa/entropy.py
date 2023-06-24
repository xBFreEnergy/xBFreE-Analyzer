import pandas as pd


class Entropy:
    def __init__(self):
        pass

    def get_data(self):
        pass

    def get_methods(self):
        pass

    def plot(self):
        pass

    def __sub__(self, other):
        """
        Subtraction operation for mutant-normal calculation
        :param other:
        :return: Entropy()
        """
        pass

    def __add__(self, other):
        """
        Addition operation for BFE calculation
        :param other:
        :return:
        """
        pass

    def __repr__(self):
        pass

    def __str__(self):
        pass



class CalculationType():
    def __init__(self):
        pass


class SubSystemType():
    def __init__(self):
        pass


class Method():
    def __init__(self):
        pass

    def get_data(self) -> pd.DataFrame:
        """
        Return the Method data as pd.DataFrame (Columns >> [ Time, Frame, [Terms], SystemPart ])
        :return:
        """
        pass

    def plot(self, kind: str):
        """
        Plot this term
        :param kind: bar | box (?)
        :return:
        """
        pass

    def barplot(self):
        """
        Equivalent to plot(kind="line")
        :return:
        """
        pass

    def boxplot(self):
        """
        Equivalent to plot(kind="hist")
        :return:
        """
        pass


class SystemPart():
    def __init__(self):
        pass

    def get_data(self) -> pd.DataFrame:
        """
        Return the SystemPart data as pd.DataFrame (Columns >> [ Time, Frame, Values, SD, SEM, Terms name ])
        :return:
        """
        pass

    def get_term(self, term):
        """
        Get selected term
        :param term:
        :return: Term class
        """
        pass

    def plot(self, kind: str):
        """
        Plot this term
        :param kind: bar
        :return:
        """
        pass

    def barplot(self):
        """
        Equivalent to plot(kind="line")
        :return:
        """
        pass


class Term():
    def __init__(self):
        pass

    def get_data(self) -> pd.DataFrame:
        """
        Return the term data as pd.DataFrame (Columns >> [ Time, Frame, Term Name ])
        :return:
        """
        pass

    def plot(self, kind: str):
        """
        Plot this term
        :param kind: line | hist | kde
        :return:
        """
        pass

    def lineplot(self):
        """
        Equivalent to plot(kind="line")
        :return:
        """
        pass

    def histplot(self):
        """
        Equivalent to plot(kind="hist")
        :return:
        """
        pass

    def kdeplot(self):
        """
        Equivalent to plot(kind="kde")
        :return:
        """
        pass
