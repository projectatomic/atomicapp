#!/usr/bin/env python

from __future__ import print_function
import os,sys
from string import Template

from yapsy.PluginManager import PluginManager

import logging

from params import Params
from utils import Utils
from constants import GLOBAL_CONF, DEFAULT_PROVIDER, ATOMIC_FILE, PARAMS_FILE

logger = logging.getLogger(__name__)

class AtomicappLevel:
    Main, Module = range(2)

def isTrue(val):
    logger.debug("Value: %s" % val)
    return True if str(val).lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'sure'] else False

class Run():
    debug = False
    dryrun = False
    atomicfile_data = None
    params = None
    answers_data = {GLOBAL_CONF: {}}
    tmpdir = None
    answers_file = None
    provider = DEFAULT_PROVIDER
    installed = False
    plugins = None
    recursive = True
    update = False
    app_path = None
    target_path = None
    app_id = None
    app = None

    def __init__(self, answers, APP, recursive = True, update = False, target_path = None, dryrun = False, debug = False, **kwargs):

        self.debug = debug
        self.dryrun = dryrun

        if os.path.exists(APP):
            self.app_path = APP
        else:
            logger.error("App path %s does not exist." % APP)


        if not self.target_path:
            if self.app_path:
                target_path = self.app_path
            else: 
                target_path = os.getcwd()

        logger.info("Target path for %s is %s" % (APP, target_path))

        self.params = Params(recursive, update, target_path)
        self.utils = Utils(self.params)

        self.answers_file = answers

        run_path = os.path.dirname(os.path.realpath(__file__))
        self.plugins = PluginManager()
        self.plugins.setPluginPlaces([os.path.join(run_path, "providers")])
        self.plugins.collectPlugins()

    def _dispatchGraph(self):
        if not "graph" in self.params.atomicfile_data:
            raise Exception("Graph not specified in %s" % ATOMIC_FILE)
        if not os.path.isdir(self.utils.getGraphDir()):
            raise Exception("Couldn't find %s directory" % GRAPH_DIR)

        for graph_item in self.params.atomicfile_data["graph"]:
            component = self.utils.getComponentName(graph_item)
            component_path = self.utils.getComponentDir(component)

        
            component_params = self.utils.getComponentConf(component)
            if os.path.isfile(component_params):
                self.params.loadParams(component_params)
            self._processComponent(component)

    def _applyTemplate(self, data, component):
        template = Template(data)
        config = self.params.get(component)
        return template.substitute(config)

    def _getProvider(self):
        for provider in self.plugins.getAllPlugins():
            module_path = provider.details.get("Core", "Module")
            if os.path.basename(module_path) == self.provider:
                return provider.plugin_object

    def _processComponent(self, component):
        path = self.utils.getProviderDir(component)
        data = None
        for artifact in os.listdir(path):
            if artifact == PARAMS_FILE:
                continue
            with open(os.path.join(path, artifact), "r") as fp:
                data = fp.read()

            logger.debug("Templating artifact %s/%s" % (path, artifact))
            data = self._applyTemplate(data, component)
        
            dst_dir = os.path.join(self.utils.tmpdir, component)
            artifact_dst = os.path.join(dst_dir, artifact)
            
            if not os.path.isdir(dst_dir):
                os.makedirs(dst_dir)
            with open(artifact_dst, "w") as fp:
                fp.write(data)

        provider = self._getProvider()
        provider.init(self.params.get(component), os.path.join(self.utils.tmpdir, component), self.debug, self.dryrun)
        provider.deploy()

    def run(self, level = AtomicappLevel.Main):
        self.params.loadAtomicfile(os.path.join(self.params.target_path, ATOMIC_FILE))

        if not self.params.loadAnswers(self.answers_file):
            logger.debug("No %s file found, using defaults" % ANSWERS_FILE)

        if not self.params.loadParams(os.path.join(self.params.target_path, PARAMS_FILE)):
            logger.error("Failed to load %s" % PARAMS_FILE)
            return
        else:
            logger.debug("Loaded params: %s" % self.params.params_data)

        config = self.params.get()
        if "provider" in config[GLOBAL_CONF]:
            self.provider = config[GLOBAL_CONF]["provider"]

        self._dispatchGraph()

    


