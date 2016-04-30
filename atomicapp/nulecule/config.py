import copy
import logging

from atomicapp.constants import (GLOBAL_CONF,
                                 LOGGER_COCKPIT,
                                 DEFAULT_PROVIDER,
                                 DEFAULT_ANSWERS,
                                 NAMESPACE_SEPARATOR)
from collections import defaultdict

cockpit_logger = logging.getLogger(LOGGER_COCKPIT)


class Config(object):
    """
    Store config data for a Nulecule or Nulecule component.

    It stores config data from different sources (answers, cli, user data)
    separately, and exposes high level interfaces to read, write data
    from it, with enforced read/write policies.
    """

    def __init__(self, namespace='', answers=None, cli=None,
                 data=None, is_nulecule=False):
        self._namespace = namespace
        self._is_nulecule = is_nulecule or False
        self._parent_ns, self._current_ns = self._split_namespace(self._namespace)
        # Store answers data
        self._answers = defaultdict(dict)
        self._answers.update(answers or {})
        # Store CLI data
        self._cli = cli or {}
        # Store data collected during runtime
        self._data = data or defaultdict(dict)
        self._context = None
        self._provider = None

    @property
    def globals(self):
        """
        Get global config params dict for a Nulecule.
        """
        d = self._answers.get(GLOBAL_CONF, {})
        d.update(self._data.get(GLOBAL_CONF, {}))
        d.update(self._cli.get(GLOBAL_CONF, {}))
        return d

    @property
    def provider(self):
        """
        Get provider name.

        Returns:
            Provider name (str)
        """
        if self._provider is None:
            self._provider = self._data[GLOBAL_CONF].get('provider') or \
                self._answers[GLOBAL_CONF].get('provider')
            if self._provider is None:
                self._data[GLOBAL_CONF]['provider'] = DEFAULT_PROVIDER
                self._provider = DEFAULT_PROVIDER

        return self._provider

    @property
    def providerconfig(self):
        """
        Get provider config info taking into account answers and cli data.
        """
        pass

    @property
    def namespace(self):
        """
        Get normalized namespace for this instance.

        Returns:
            Current namespace (str).
        """
        return self._namespace or GLOBAL_CONF

    def set(self, key, value):
        """
        Set value for a key in the current namespace.

        Args:
            key (str): Key
            value (str): Value.
        """
        self._data[self.namespace][key] = value

    def get(self, key):
        """
        Get value for a key from data accessible from the current namespace.

        TODO: Improved data inheritance model. It makes sense for a component
        to be able to access data from it's sibling namespaces and children
        namespaces.

        Args:
            key (str): Key

        Returns:
            Value for the key, else None.
        """
        return (
            self._data[self.namespace].get(key) or
            (self._data[self._parent_ns].get(key) if self._parent_ns else None) or
            self._data[GLOBAL_CONF].get(key) or
            self._answers[self.namespace].get(key) or
            (self._answers[self._parent_ns].get(key) if self._parent_ns else None) or
            self._answers[GLOBAL_CONF].get(key)
        )

    def context(self):
        """
        Get context to render artifact files in a Nulecule component.

        TODO: Improved data inheritance model. Data from siblings and children
        namespaces should be available in the context to render an artifact
        file in the current namespace.
        """
        if self._context is None:
            self._context = {}
            self._context.update(copy.copy(self._data[GLOBAL_CONF]))
            self._context.update(copy.copy(self._data[self.namespace]))

            self._context.update(copy.copy(self._answers[GLOBAL_CONF]))
            self._context.update(copy.copy(self._answers[self.namespace]))
        return self._context

    def runtime_answers(self):
        """
        Get runtime answers.

        Returns:
            A defaultdict containing runtime answers data.
        """
        answers = defaultdict(dict)
        answers.update(copy.deepcopy(DEFAULT_ANSWERS))
        answers['general']['provider'] = self.provider

        for key, value in self._answers.items():
            answers[key].update(value)

        for key, value in self._data.items():
            answers[key].update(value)

        # Remove empty sections for answers
        for key, value in answers.items():
            if value is None:
                answers.pop(key, None)

        return answers

    def clone(self, namespace):
        """
        Create a new config instance in the specified namespace.

        Args:
            name (str): Name of the child component

        Returns:
            A Config instance.
        """
        config = Config(namespace=namespace,
                        answers=self._answers,
                        cli=self._cli,
                        data=self._data)
        return config

    def _split_namespace(self, namespace):
        """
        Split namespace to get parent and current namespace in a Nulecule.
        """
        if self._is_nulecule:
            return '', namespace
        words = namespace.rsplit(NAMESPACE_SEPARATOR, 1)
        parent, current = '', ''
        if len(words) == 2:
            parent, current = words[0], words[1]
        else:
            parent, current = '', words[0]
        return parent, current

    def __eq__(self, obj):
        """
        Check equality of config instances.
        """
        if self._namespace == obj._namespace or self._answers == obj._answers or self._data == obj._data or self._cli == obj._cli:
            return True
        return False
