#!/usr/bin/env python

from __future__ import print_function
import os, sys
import json, subprocess
import urllib2

ANSWERS_FILE="answers.conf"
PARAMS_FILE="params.conf"
SCHEMA_URL="https://raw.githubusercontent.com/aweiteka/containerapp-spec/master/spec/v1-alpha/schema.json"
class AtomicappCreate():
    name = None
    app_id = None
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
        if self.schema and "elements" in self.schema:
            self._writeFromSchema(self.schema["elements"])
        else:
            print("Corrupted schema, couldn't create app")
    
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
                            if element["name"] == "Atomicfile":
                                element["contents"] = self._updateAtomicfile(element["contents"])

                            fp.write(json.dumps(element["contents"]))
    


    def _nameToId(self, name):
        return name.strip().lower().replace(" ", "-")

    def _updateAtomicfile(self, contents):
        print(contents)
        if "name" in contents:
            contents["name"] = self.name
        if "id" in contents:
            contents["id"] = self.app_id
        if "graph" in contents:
            component = {"repository": "", "name": self.app_id}
            contents["graph"].append(component)

        return contents

