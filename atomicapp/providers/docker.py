from atomicapp.plugin import Provider, ProviderFailedException
import os
import subprocess

import logging

logger = logging.getLogger(__name__)


class DockerProvider(Provider):
    key = "docker"

    def init(self):

        cmd_check = ["docker", "version"]
        try:
            docker_version = subprocess.check_output(cmd_check).split("\n")
        except Exception as ex:
            raise ProviderFailedException(ex)

        client = ""
        server = ""
        for line in docker_version:
            if line.startswith("Client API version"):
                client = line.split(":")[1]
            if line.startswith("Server API version"):
                server = line.split(":")[1]

        if client > server:
            msg = ("Docker version in app image (%s) is higher than the one "
                   "on host (%s). Please update your host." % (client, server))
            raise ProviderFailedException(msg)

    def deploy(self):
        for artifact in self.artifacts:
            artifact_path = os.path.join(self.path, artifact)
            label_run = None
            with open(artifact_path, "r") as fp:
                label_run = fp.read().strip()

            cmd = label_run.split()

            if self.dryrun:
                logger.info("DRY-RUN: %s", " ".join(cmd))
            else:
                subprocess.check_call(cmd)
