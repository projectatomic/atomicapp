class NuleculeConfig(object):
    pass


class NuleculeBase(object):

    def load(self):
        pass

    def run(self, provider):
        raise NotImplementedError

    def stop(self, provider):
        raise NotImplementedError

    def install(self):
        raise NotImplementedError

    def uninstall(self):
        raise NotImplementedError


class Nulecule(NuleculeBase):
    """
    This represents a Nulecule application. A Nulecule instance can have
    instances of Nulecule and Nulecule as components. A Nulecule instance
    knows everything about itself and its componenents, but does not have
    access to it's parent's scope.
    """
    def __init__(self, id, specversion, metadata, graph, requirements=None,
                 params=None, config=None):
        self.id = id
        self.specversion = specversion
        self.metadata = metadata
        self.graph = graph
        self.requirements = requirements
        self.params = params
        self.load()

    def load(self):
        self.components = self.load_components()
        self.config = self.load_config()

    def load_components(self, graph):
        components = []
        for item in graph:
            components.append(NuleculeComponent(item))

    def run(self):
        # run the Nulecule application
        pass

    def stop(self):
        # stop the Nulecule application
        pass

    def install(self):
        # install the Nulecule application
        pass

    def uninstall(self):
        # uninstall the Nulecule application
        pass


class NuleculeComponent(NuleculeBase):
    """
    Represents a local service in a Nulecule application. It receives props
    from it's parent and can add new props and override props at it's local
    scope. It does not have direct access to props of sibling Nulecule
    components, but can request the value of sibling's property from it's
    parent.
    """
    pass
