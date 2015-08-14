"""
 Copyright 2015 Red Hat, Inc.

 This file is part of Atomic App.

 Atomic App is free software: you can redistribute it and/or modify
 it under the terms of the GNU Lesser General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Atomic App is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Lesser General Public License for more details.

 You should have received a copy of the GNU Lesser General Public License
 along with Atomic App. If not, see <http://www.gnu.org/licenses/>.
"""

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
