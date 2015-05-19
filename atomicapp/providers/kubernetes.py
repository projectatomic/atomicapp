from atomicapp.plugin import Provider, ProviderFailedException

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
                if self.dryrun:
                    logger.info("DRY-RUN: link /etc/kubernetes from /host/etc/kubernetes")
                else:
                    os.symlink("/host/etc/kubernetes", "/etc/kubernetes")

        if not self.dryrun:
            if not os.access(self.kubectl, os.X_OK):
                raise ProviderFailedException("Command kubectl not found")

    def _callK8s(self, path):
        cmd = [self.kubectl, "create", "-f", path]

        if self.dryrun:
            logger.info("DRY-RUN: %s" % " ".join(cmd))
        else:
            subprocess.check_call(cmd)

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
                raise ProviderFailedException("Malformed kube file")

        for artifact in kube_order:
            if not kube_order[artifact]:
                continue

            k8s_file = os.path.join(self.path, kube_order[artifact])
            self._callK8s(k8s_file)
