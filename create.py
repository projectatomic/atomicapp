#!/usr/bin/python

from __future__ import print_function
import os, sys
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import json, subprocess
import urllib2

ANSWERS_FILE="answers.conf"
PARAMS_FILE="params.conf"
SCHEMA_URL="https://raw.githubusercontent.com/aweiteka/containerapp-spec/master/spec/v1-alpha/schema.json"
class AtomicappCreate():
    Atomicfile = """
    {
        "specversion": "v1-alpha", 
        "name": "%s",
        "id": "%s",
        "appversion": "0.0.1",
        "description": "My App",
        "graph": [
            "%s"
        ]
    }
    """
    parameters = """[general]

"""
    dockerfile = """
FROM scratch

MAINTAINER vpavlin <vpavlin@redhat.com>

ADD / /application-entity/
"""
    name = None
    dryrun = False
    schema = None
    def __init__(self, name, schema = None, dryrun = False):
        self.name = name
        self.app_id = self._nameToId(name)
        self.dryrun = dryrun

        if not schema: 
            schema = SCHEMA_URL
        
        if not os.path.isfile(schema):
            response = urllib2.urlopen(schema)
            with open(os.path.basename(schema), "w") as fp:
                fp.write(response.read())
                schema = os.path.basename(schema)
        
        with open(schema, "r") as fp:
            self.schema = json.load(fp)

    def create(self):
        if self.schema:
            self._writeFromSchema(self.schema["elements"])
        else:
            self._writeAtomicfile()
            self._createGraph()
            self._writeParamsFile(os.getcwd())
            self._writeDockerfile()

    def build(self, tag):
        if not tag:
            tag = self.app_id

        cmd = ["docker", "build", "-t", tag, "."]
        if self.dryrun:
            print("Build: %s" % " ".join(cmd))
        else:
            subprocess.call(cmd)


    def _writeFromSchema(self, elements):
        for element in elements:
            value = element["value"]
            if not element["contents"] and not value:
                continue
            if element["name"] == "application":
                value = self.app_id
            print("Writing %s" % element["name"])
            if element["elementType"] == "directory":
                os.mkdir(value)
                os.chdir(value)
                self._writeFromSchema(element["contents"])
                os.chdir("..")
            elif element["elementType"] == "file":
                with open(value, "w") as fp:
                    if element["contents"]:
                        if element["contentType"] == "text/plain":
                            fp.write(element["contents"])
                        elif element["contentType"] == "application/json":
                            fp.write(json.dumps(element["contents"]))
    


    def _nameToId(self, name):
        return name.strip().lower().replace(" ", "-")

    def _writeAtomicfile(self):
        with open(os.path.join(os.getcwd(), "Atomicfile"), "w") as fp:
            fp.write(json.dumps(json.loads(self.Atomicfile % (self.name, self.app_id, self.app_id))))

    def _writeDockerfile(self):
         with open(os.path.join(os.getcwd(), "Dockerfile"), "w") as fp:
             fp.write(self.dockerfile)

    def _writeParamsFile(self, path):
        with open(os.path.join(path, PARAMS_FILE), "w") as fp:
            fp.write(self.parameters)

    def _createGraph(self):
        app_path = os.path.join(os.getcwd(), "graph", "provider", self.app_id)
        os.makedirs(app_path)
        self._writeParamsFile(app_path)


if __name__ == "__main__":
    parser = ArgumentParser(description='Create a Container App specification complient project', formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--debug", dest="debug", default=False, action="store_true", help="Debug")
    parser.add_argument("--dry-run", dest="dryrun", default=False, action="store_true", help="Don't call k8s")
    parser.add_argument("-a", "--answers", dest="answers", default=os.path.join(os.getcwd(), ANSWERS_FILE), help="Path to %s" % ANSWERS_FILE)
    parser.add_argument("NAME", help="App name")

    args = parser.parse_args()

    ac = AtomicappCreate(args.NAME)
    ac.create()

    sys.exit(0)
