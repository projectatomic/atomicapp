#!/usr/bin/python

from __future__ import print_function
import os,sys
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from string import Template
import tempfile
import subprocess
#import anymarkup
import distutils.dir_util
import ConfigParser, json

from yapsy.PluginManager import PluginManager

ATOMIC_FILE="Atomicfile"
PARAMS_FILE="params.conf"
ANSWERS_FILE="answers.conf"
GRAPH_DIR="graph"
APP_ENT_PATH="application-entity"
GLOBAL_CONF="general"
DEFAULT_PROVIDER="kubernetes"

class AtomicappLevel:
    Main, Module = range(2)

class Atomicapp():
    debug = False
    dryrun = False
    atomicfile_data = None
    params_data = None
    answers_data = {GLOBAL_CONF: {}}
    tmpdir = None
    app_name = None
    answers_file = None
    provider = DEFAULT_PROVIDER
    installed = False
    plugins = None

    def __init__(self, answers, app, dryrun = False, debug = False):

        run_path = os.path.dirname(os.path.realpath(__file__))
        self.debug = debug
        self.dryrun = dryrun

        self.tmpdir = tempfile.mkdtemp(prefix="appent-%s" % self._getModuleName(app))
        if self.debug:
            print(self.tmpdir)

        self.app_name = app
        self.answers_file = answers

        self.plugins = PluginManager()
        self.plugins.setPluginPlaces([os.path.join(run_path, "providers")])
        self.plugins.collectPlugins()

    def _getModuleName(self, app):
        return os.path.basename(app).split(":")[0]

    def _sanitizeName(self, app):
        return app.replace("/", "-")

    def _mergeConfig(self):

        config = self.params_data
        if self.answers_data:
            if config:
                config.update(self.answers_data)
            else:
                config = self.answers_data

        return config

    def _loadAtomicfile(self, path = None):
        if not os.path.exists(path):
            return None
        
        with open(path, "r") as fp:
            self.atomicfile_data = json.load(fp)

        return self.atomicfile_data

    def _loadParams(self, path = None):
        if not os.path.exists(path):
            return None

        config = ConfigParser.ConfigParser()

        data = {}
        with open(path, "r") as fp:
            config.readfp(fp)

            for section in config.sections():
                data[section] = dict(config.items(section))

        if self.params_data:
                self.params_data.update(data)
        else:
            self.params_data = data

        return self.params_data

    def _loadAnswers(self, path = None):
        if not os.path.exists(path):
            return None

        config = ConfigParser.ConfigParser()

        data = {}
        with open(path, "r") as fp:
            config.readfp(fp)

            for section in config.sections():
                data[section] = dict(config.items(section))
        
        self.answers_data = data

        return self.answers_data

    def _getComponentDir(self, component):
        return os.path.join(os.getcwd(), GRAPH_DIR, component)

    def _getProviderDir(self, component):
#FIXME add provider resolution by answers file
        return os.path.join(os.getcwd(), GRAPH_DIR, component, self.provider)

    def _getTmpAppDir(self):
        return os.path.join(self.tmpdir, APP_ENT_PATH)

    def _dispatchGraph(self):
        if not "graph" in self.atomicfile_data:
            raise Exception("Graph not specified in %s" % ATOMIC_FILE)
        if not os.path.isdir(os.path.join(os.getcwd(), GRAPH_DIR)):
            raise Exception("Couldn't find %s directory" % GRAPH_DIR)

        for component in self.atomicfile_data["graph"]:
            component_path = self._getComponentDir(component)
            if not os.path.isdir(component_path):
                print("Pulling %s" % component)
                component_atomicapp = Atomicapp(self.answers_file, component, self.dryrun, self.debug)
                component = component_atomicapp.install(component, AtomicappLevel.Module)
                component_path = self._getComponentDir(component)

            component_params = os.path.join(component_path, self.provider, PARAMS_FILE)
            if os.path.isfile(component_params):
                self._loadParams(component_params)
            self._processComponent(component)

    def _applyTemplate(self, data, component):
        template = Template(data)

        config = self._mergeConfig()
        component_config = config[component] if component in config else None

        return template.substitute(component_config)

    def _getProvider(self):
        for provider in self.plugins.getAllPlugins():
            module_path = provider.details.get("Core", "Module")
            if os.path.basename(module_path) == self.provider:
                return provider.plugin_object

    def _processComponent(self, component):
        path = os.path.join(self._getProviderDir(component))
        data = None
        for artifact in os.listdir(path):
            if artifact == PARAMS_FILE:
                continue
            with open(os.path.join(path, artifact), "r") as fp:
                data = fp.read()

#            print("Data: %s" % data)

            data = self._applyTemplate(data, component)
        
            dst_dir = os.path.join(self.tmpdir, component)
            artifact_dst = os.path.join(dst_dir, artifact)
            
            if not os.path.isdir(dst_dir):
                os.makedirs(dst_dir)
            with open(artifact_dst, "w") as fp:
                fp.write(data)

        provider = self._getProvider()
        provider.init(self._mergeConfig(), os.path.join(self.tmpdir, component), self.debug, self.dryrun)
        provider.deploy()


    def _pullApp(self, app):
        config = self._mergeConfig()
        
        if GLOBAL_CONF in config and "registry" in config[GLOBAL_CONF]:
            print("Adding registry %s" % config[GLOBAL_CONF]["registry"])
            app = os.path.join(config[GLOBAL_CONF]["registry"], app)

        pull = ["docker", "pull", app]
        if False and subprocess.call(pull) != 0:
            print("Couldn't pull %s" % app)
            sys.exit(1)
            
        name = self._getModuleName(app)
        
        create = ["docker", "create", "--name", name, app, "nop"]
        subprocess.call(create)
        cp = ["docker", "cp", "%s:/%s" % (name, APP_ENT_PATH), self.tmpdir]
        subprocess.call(cp)

        rm = ["docker", "rm", name]
        subprocess.call(rm)

    def _populateMainApp(self):
        print("Copying app %s" % self._getModuleName(self.app_name))
        distutils.dir_util.copy_tree(os.path.join(self.tmpdir, APP_ENT_PATH), os.getcwd())
    
    def _populateModule(self):

        data_list = [
                "graph/%s/" % self.app_id,
                "Atomicfile",
                "params.conf"
                ]
        
        print("Copying module %s" % self._getModuleName(self.app_name))
        for item in data_list:
            path = os.path.join(self.tmpdir, APP_ENT_PATH, item)
            if os.path.isdir(path):
                distutils.dir_util.copy_tree(path, os.path.join(os.getcwd(), GRAPH_DIR, self.app_id))
            else:
                distutils.file_util.copy_file(path, os.path.join(os.getcwd(), GRAPH_DIR, self.app_id, item))

    def run(self, app, level = AtomicappLevel.Main):
        print(app)
        if not self.installed:
            self.install(app, level)

        if not self._loadAtomicfile(os.path.join(os.getcwd(), ATOMIC_FILE)):
            print("Failed to load %s" % ATOMIC_FILE)
            return

        if self.debug:
            print(self.atomicfile_data)

        if not self._loadParams(os.path.join(os.getcwd(), PARAMS_FILE)):
            print("Failed to load %s" % PARAMS_FILE)
            return

        config = self._mergeConfig()
        if "provider" in config[GLOBAL_CONF]:
            self.provider = config[GLOBAL_CONF]["provider"]

        if self.debug:
            print(self.params_data)

        self._dispatchGraph()

    def install(self, app, level = AtomicappLevel.Main):

        if not self._loadAnswers(self.answers_file):
            print("No %s file found, using defaults" % ANSWERS_FILE)

        if not os.path.exists(app):
            self._pullApp(app)
            with open(os.path.join(self._getTmpAppDir(), ATOMIC_FILE), "r") as fp:
                self.atomicfile_data = json.load(fp)
                print(self.atomicfile_data)

            self.app_id = self.atomicfile_data["id"]

            if level == AtomicappLevel.Main:
                self._populateMainApp()
            elif level == AtomicappLevel.Module:
                self._populateModule()

        self.installed = True
        return self.app_id

if __name__ == "__main__":
    parser = ArgumentParser(description='Run an application defined by Atomicfile', formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--debug", dest="debug", default=False, action="store_true", help="Debug")
    parser.add_argument("--dry-run", dest="dryrun", default=False, action="store_true", help="Don't call k8s")
    parser.add_argument("-a", "--answers", dest="answers", default=os.path.join(os.getcwd(), ANSWERS_FILE), help="Path to %s" % ANSWERS_FILE)
    parser.add_argument("app", help="App to run")

    args = parser.parse_args()

    ae = Atomicapp(args.answers, args.app, args.dryrun, args.debug)
    ae.run(args.app)

    sys.exit(0)
