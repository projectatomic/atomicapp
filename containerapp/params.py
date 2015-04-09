#!/usr/bin/env python

import anymarkup
import os
import logging

logger = logging.getLogger("params")

PARAMS_KEY="params"
ATOMIC_FILE="Atomicfile"
PARAMS_FILE="params.conf"
ANSWERS_FILE="answers.conf"

class Params():
    answers_data = None
    params_data = None
    
    def __init__(self):
        pass


    def loadParams(self, data = {}):
        logger.debug("Data %s" % data)
        if os.path.exists(data):
            logger.debug("Path given, loading %s" % data)
            data = anymarkup.parse_file(data)

        if "specversion" in data:
            logger.debug("Params merged with %s" % ATOMICFILE)
            data = data[PARAMS_KEY]
        else:
            logger.debug("Params in separate file")

        if self.params_data:
                self._update(data)
        else:
            self.params_data = data

        return self.params_data

    def loadAnswers(self, data = {}):
        if os.path.exists(data):
            logger.debug("Path given, loading %s" % data)
            data = anymarkup.parse_file(data)

        self.answers_data = data
        return self.answers_data

    def get(self, component = None):
        params = None
        if component:
            params = self._mergeParamsComponent(component)
        else:
            params = self._mergeParams()

        return params

    def _mergeParams(self):
        config = self.params_data
        if self.answers_data:
            if config:
                config = self._update(config, self.answers_data)
            else:
                config = self.answers_data

        return config

    def _mergeParamsComponent(self, component):
        config = self._mergeParams()
        component_config = config[GLOBAL_CONF] if GLOBAL_CONF in config else {}
        if component in config:
            component_config = self._update(component_config, config[component])

        return component_config

    def _update(self, new_dict):
        for key, val in new_dict.iteritems():
            if isinstance(val, collections.Mapping):
                tmp = _update(self.params_data.get(key, { }), val)
                self.params_data[key] = tmp
            elif isinstance(val, list):
                self.params_data[key] = (self.params_data[key] + val)
            else:
                self.params_data[key] = new_dict[key]
        return self.params_data
