from yapsy.IPlugin import IPlugin

import os, subprocess

class DockerProvider(IPlugin):
    config = None
    component_dir = None
    debug = None
    dryrun = None
    def init(self, config, component_dir, debug, dryrun):
        self.confif = config
        self.component_dir = component_dir
        self.debug = debug
        self.dryrun = dryrun

    def deploy(self):
        label_run_file = os.path.join(self.component_dir, "label_run")
        label_run = None
        with open(label_run_file, "r") as fp:
            label_run = fp.read().strip()

        cmd = label_run.split(" ")

        if self.dryrun:
            print("Run: %s" % " ".join(cmd))
        else:
            subprocess.call(cmd)

    def print_name(self):
        print "This is plugin 1"
