from atomicapp.plugin import Provider, ProviderFailedException

from collections import OrderedDict
import os, anymarkup, subprocess
from distutils.spawn import find_executable

import logging

logger = logging.getLogger(__name__)

class OpenShiftProvider(Provider):
    key = "openshift"

    cli = find_executable("osc")
    config_file = None
    template_data = None
    def init(self):
        if not self.dryrun:
            if self.container:
                self.cli = "/host/%s" % self.cli
            if not os.access(self.cli, os.X_OK):
                raise ProviderFailedException("Command %s not found" % self.cli)

        if "openshiftconfig" in self.config:
            self.config_file = self.config["openshiftconfig"]

        if not self.config_file or not os.access(self.config_file, os.R_OK):
            raise ProviderFailedException("Cannot access configuration file %s" % self.config_file)

    def _callCli(self, path):
        cmd = [self.cli, "--config=%s" % self.config_file, "create", "-f", path]

        if self.dryrun:
            logger.info("Calling: %s", " ".join(cmd))
        else:
            subprocess.check_call(cmd)

    def _processTemplate(self, path):
        cmd = [self.cli, "--config=%s" % self.config_file, "process", "-f", path]

        name = "config-%s" % os.path.basename(path)
        output_path = os.path.join(self.path, name)
        if not self.dryrun:
            output = subprocess.check_output(cmd)
            logger.debug("Writing processed template to %s", output_path)
            with open(output_path, "w") as fp:
                fp.write(output)
        return output_path

    def loadArtifact(self, path):
        data = super(self.__class__, self).loadArtifact(path)
        self.template_data = anymarkup.parse(data, force_types=None)
        if "kind" in self.template_data and self.template_data["kind"].lower() == "template":
            if "parameters" in self.template_data:
                return anymarkup.serialize(self.template_data["parameters"], format="json")

        return data

    def saveArtifact(self, path, data):
        if self.template_data:
            if "kind" in self.template_data and self.template_data["kind"].lower() == "template":
                if "parameters" in self.template_data:
                    passed_data = anymarkup.parse(data, force_types=None)
                    self.template_data["parameters"] = passed_data
                    data = anymarkup.serialize(self.template_data, format=os.path.splitext(path)[1].strip(".")) #FIXME

        super(self.__class__, self).saveArtifact(path, data)

    def deploy(self):
        kube_order = OrderedDict([("service", None), ("rc", None), ("pod", None)]) #FIXME
        for artifact in self.artifacts:
            data = None
            artifact_path = os.path.join(self.path, artifact)
            with open(artifact_path, "r") as fp:
                data = anymarkup.parse(fp, force_types=None)
            if "kind" in data:
                if data["kind"].lower() == "template":
                    artifact = self._processTemplate(artifact_path)
                kube_order[data["kind"].lower()] = artifact
            else:
                raise ProviderFailedException("Malformed artifact file")

        for artifact in kube_order:
            if not kube_order[artifact]:
                continue

            k8s_file = os.path.join(self.path, kube_order[artifact])
            self._callCli(k8s_file)
