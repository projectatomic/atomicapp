from yapsy.IPlugin import IPlugin

from collections import OrderedDict
import os, json, subprocess

class KubernetesProvider(IPlugin):
    config = None
    component_dir = None
    debug = None
    dryrun = None
    def init(self, config, component_dir, debug, dryrun):
        self.confif = config
        self.component_dir = component_dir
        self.debug = debug
        self.dryrun = dryrun

    def _callK8s(self, path):
        cmd = ["kubectl", "create", "-f", path, "--api-version=v1beta1"]
        print("Calling: %s" % " ".join(cmd))

        if self.dryrun:
            return True
        else:
            if subprocess.call(cmd) == 0:
                return True
        
        return False

    def deploy(self):
        kube_order = OrderedDict([("service", None), ("rc", None), ("pod", None)]) #FIXME
        for artifact in os.listdir(self.component_dir):
            data = None
            with open(os.path.join(self.component_dir, artifact), "r") as fp:
                data = json.load(fp)
            if "kind" in data:
                kube_order[data["kind"].lower()] = artifact
            else:
                print("Malformed kube file")

        for artifact in kube_order:
            if not kube_order[artifact]:
                continue
        
            k8s_file = os.path.join(self.component_dir, kube_order[artifact])
            self._callK8s(k8s_file)
