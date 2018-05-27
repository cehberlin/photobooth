
from abc import ABCMeta, abstractmethod


class Decoration(object):
    """
    Base class for all decorations
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def apply(self, filter):
        """
        Override this method to apply an decoration
        :param filter: The filter that is decorated
        :return:
        """
        pass