class GenericClassFactory(object):
    """
    Factory for the registration and creation of classes

    Usage:
    # Create singleton factory object
    example_factory = GenericClassFactory(YourAbstractClass)

    def get_user_io_factory():
        return example_factory;

    example_factory.register_algorithm(id_class='example_id', class_obj=ChildOfYourAbstractClass)
    """

    def __init__(self, abstract_class_type):
        self._algorithms = {}
        self._abstract_class_type = abstract_class_type

    def register_algorithm(self, id_class, class_obj):
        """
        Register an algorithm in the factory under the given ID
        Algorithm has to be a subclass of self._abstract_class_type
        :param id_class: ID for the algorithm
        :type id_class: str
        :param class_obj: the algorithm class
        :type class_obj: class that inherits from self._abstract_class_type
        :return:
        """
        if not issubclass(class_obj, self._abstract_class_type):
            assert ("Algo is not subclass of " + str(self._abstract_class_type))
        if self._algorithms.has_key(id_class):
            assert ("Algorithm ID already in use")
        else:
            self._algorithms[id_class] = class_obj

    def create_algorithm(self, id_class, **kwargs):
        """
        Initialize the algorithm with the given ID
        :param id_class: the id of the impl that should be created
        :type id_class str
        :return: a specific instance of self._abstract_class_type
        """
        if not self._algorithms.has_key(id_class):
            raise LookupError("Cannot find class_id: " + id_class)
        else:
            return self._algorithms[id_class](**kwargs)