from atomicapp.plugin import Provider

from collections import OrderedDict
import os, anymarkup, subprocess

import logging

logger = logging.getLogger(__name__)

class KubernetesProvider(Provider):
    key = "kubernetes"

    kubectl = "kubectl"
    def init(self):
        if self.container:
            self.kubectl = "/host/usr/bin/kubectl"
            if not os.path.exists("/etc/kubernetes"):
                os.symlink("/host/etc/kubernetes", "/etc/kubernetes")

    def _callK8s(self, path):
        cmd = [self.kubectl, "create", "-f", path]
        logger.info("Calling: %s" % " ".join(cmd))

        if not self.dryrun:
            subprocess.check_call(cmd) == 0

    def deploy(self):
        kube_order = OrderedDict([("service", None), ("rc", None), ("pod", None)]) #FIXME
        for artifact in self.artifacts:
            data = None
            with open(os.path.join(self.path, artifact), "r") as fp:
                logger.debug(os.path.join(self.path, artifact))
                data = anymarkup.parse(fp)
            if "kind" in data:
                kube_order[data["kind"].lower()] = artifact
            else:
                logger.info("Malformed kube file")

        for artifact in kube_order:
            if not kube_order[artifact]:
                continue
        
            k8s_file = os.path.join(self.path, kube_order[artifact])
            self._callK8s(k8s_file)
