#!/usr/bin/python

from __future__ import print_function
import os,sys
import json
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import ConfigParser
from string import Template
import tempfile

ATOMIC_FILE="Atomicfile"
PARAMS_FILE="params.ini"
ANSWERS_FILE="answers.ini"
K8S_DIR="Kubernetes"


class AppEnt():
    debug = False
    atomicfile_data = None
    params_data = None
    answers_data = None
    tmpdir = None
    def __init__(self, answers, debug = False):
        self.debug = debug

        self.tmpdir = tempfile.mkdtemp(prefix="appent-")

        if not self._loadAtomicfile(os.path.join(os.getcwd(), ATOMIC_FILE)):
            print("Failed to load %s" % ATOMIC_FILE)
            return

        if self.debug:
            print(self.atomicfile_data)

        if not self._loadParams(os.path.join(os.getcwd(), PARAMS_FILE)):
            print("Failed to load %s" % PARAMS_FILE)
            return
        
        if self.debug:
            print(self.params_data.sections())

        if not self._loadAnswers(answers):
            print("No %s file found, using defaults" % ANSWERS_FILE)


        self._dispatchGraph()


        

    def _loadAtomicfile(self, path = None):
        if not os.path.exists(path):
            return None

        with open(path, "r") as fp:
            self.atomicfile_data = json.load(fp)

        return self.atomicfile_data

    def _loadParams(self, path = None):
        if not os.path.exists(path):
            return None

        self.params_data = ConfigParser.ConfigParser()
        self.params_data.read([path])

        return self.params_data

    def _loadAnswers(self, path = None):
        if not os.path.exists(path):
            return None

        self.answers_data = ConfigParser.ConfigParser()
        self.answers_data.read([path])

        return self.answers_data

    def _getComponentDir(self, component):
        return os.path.join(os.getcwd(), K8S_DIR, component)

    def _dispatchGraph(self):
        if not "graph" in self.atomicfile_data:
            raise Exception("Graph not specified in %s" % ATOMIC_FILE)
        if not os.path.isdir(os.path.join(os.getcwd(), K8S_DIR)):
            raise Exception("Couldn't find %s directory" % K8S_DIR)

        for component in self.atomicfile_data["graph"]:
            component_path = self._getComponentDir(component)
            if os.path.isdir(component_path):
                self._processComponent(component)
            else:
                raise Exception("Data for component %s is missing" % component)

    def _applyTemplate(self, data, component):
        template = Template(data)
        if not self.params_data.has_section(component):
            print("No defaults for %s" % component)
            return data

        d = dict(self.params_data.items(component))
        if self.answers_data and self.answers_data.has_section(component):
            d.update(dict(self.answers_data.items(component)))

        return template.substitute(d)

    def _processComponent(self, component):
        kube_artifacts = ["service", "rc", "pod"] #FIXME
        for artifact in kube_artifacts:
            filename = "%s-%s.json" % (component, artifact)
            path = os.path.join(self._getComponentDir(component), filename)
            if not os.path.exists(path):
                continue
            data = None
            with open(path) as fp:
                data = self._applyTemplate(fp.read(), component)
        
            k8s_file = os.path.join(self.tmpdir, filename)
            with open(k8s_file, "w") as fp:
                fp.write(data)

            print("Calling k8s for %s" % k8s_file)


if __name__ == "__main__":
    parser = ArgumentParser(description='Run an application defined by Atomicfile', formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--debug", dest="debug", default=False, action="store_true", help="Debug")
    parser.add_argument("-a", "--answers", dest="answers", default=os.path.join(os.getcwd(), ANSWERS_FILE), help="Path to %s" % ANSWERS_FILE)

    args = parser.parse_args()

    ae = AppEnt(args.answers, args.debug)

    sys.exit(0)
