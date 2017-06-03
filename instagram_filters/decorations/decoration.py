

class Decoration(object):
    """
    Base class for all decorations that provides access to the filter object
    """

    def __init__(self, filter):
        self._filter=filter