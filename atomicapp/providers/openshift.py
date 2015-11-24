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
from atomicapp.utils import printErrorStatus

import os
import anymarkup
import requests
import urlparse
from atomicapp.constants import PROVIDER_API_KEY, ACCESS_TOKEN_KEY, DEFAULT_NAMESPACE

import logging

logger = logging.getLogger(__name__)


class OpenShiftProvider(Provider):
    key = "openshift"
    cli_str = "oc"
    cli = None
    config_file = None
    template_data = None
    providerapi = "https://127.0.0.1:8443"
    openshift_api_version = "v1"
    openshift_api = None
    kubernetes_api_version = "v1"
    kubernetes_api = None
    access_token = None
    namespace = DEFAULT_NAMESPACE

    # Parsed artifacts. Key is kind of artifacts. Value is list of artifacts.
    openshift_artifacts = {}

    def init(self):
        if self.config.get(PROVIDER_API_KEY):
            self.providerapi = self.config.get(PROVIDER_API_KEY)

        self.openshift_api = urlparse.urljoin(self.providerapi, "oapi/")
        self.openshift_api = urlparse.urljoin(self.openshift_api, "%s/" % self.openshift_api_version)

        self.kubernetes_api = urlparse.urljoin(self.providerapi, "api/")
        self.kubernetes_api = urlparse.urljoin(self.kubernetes_api, "%s/" % self.kubernetes_api_version)

        if self.config.get(ACCESS_TOKEN_KEY):
            self.access_token = self.config.get(ACCESS_TOKEN_KEY)
        else:
            raise ProviderFailedException("No %s specified" % ACCESS_TOKEN_KEY)

        if self.config.get("namespace"):
            self.namespace = self.config.get("namespace")

        logger.debug("openshift_api = %s", self.openshift_api)

        self._process_artifacts()

    def deploy(self):
        logger.debug("starting deploy")
        for kind, objects in self.openshift_artifacts.iteritems():
            for artifact in objects:
                # use namespace from artifact if is specified tehere
                # otherwise use namespace from answers.conf or default namespace
                if "metadata" in artifact and "namespace" in artifact["metadata"]:
                    namespace = artifact["metadata"]["namespace"]
                else:
                    namespace = self.namespace

                url = self._get_url(namespace, kind)

                if self.dryrun:
                    logger.info("DRY-RUN: %s", url)
                    continue
                res = requests.post(url, json=artifact, verify=False)
                if res.status_code == 201:
                    logger.info(" %s sucessfully deployed.", res.content)
                else:
                    msg = "%s %s" % (res.status_code, res.content)
                    logger.error(msg)
                    raise ProviderFailedException(msg)

    def undeploy(self):
        logger.debug("starting undeploy")
        for kind, objects in self.openshift_artifacts.iteritems():
            for artifact in objects:
                # use namespace from artifact if is specified tehere
                # otherwise use namespace from answers.conf or default namespace
                if "metadata" in artifact and "namespace" in artifact["metadata"]:
                    namespace = artifact["metadata"]["namespace"]
                else:
                    namespace = self.namespace

                if "metadata" in artifact and "namespace" in artifact["metadata"]:
                    name = artifact["metadata"]["name"]
                else:
                    raise ProviderFailedException("Cannot undeploy. There is no name in artifact")

                url = self._get_url(namespace, kind, name)

                if self.dryrun:
                    logger.info("DRY-RUN: %s", url)
                    continue

                res = requests.delete(url, verify=False)
                if res.status_code == 200:
                    logger.info(" %s sucessfully undeployed.", res.content)
                else:
                    msg = "%s %s" % (res.status_code, res.content)
                    logger.error(msg)
                    raise ProviderFailedException(msg)

    def _process_artifacts(self):
        """
        process artifact files
        save parsed artifacts to self.openshift_artifacts
        """
        for artifact in self.artifacts:
            logger.debug("Procesesing artifact: %s", artifact)
            data = None
            with open(os.path.join(self.path, artifact), "r") as fp:
                try:
                    data = anymarkup.parse(fp)
                    # kind has to be specified in artifact
                    if "kind" not in data.keys():
                        raise ProviderFailedException(
                            "Error processing %s artifact. There is no kind" % artifact)
                    kind = data['kind'].title()
                except Exception:
                    msg = "Error processing %s artifact. Error:" % os.path.join(
                        self.path, artifact)
                    printErrorStatus(msg)
                    raise
                # add parsed artifact to dict
                if kind not in self.openshift_artifacts.keys():
                    self.openshift_artifacts[kind] = []
                self.openshift_artifacts[kind].append(data)

    def _get_url(self, namespace, kind, name=None):
        """
        generate url
        return either openshift api url or kubernetes api url for given kind and namespace
        """
        url = None

        if kind == "Deploymentconfig":
            url = urlparse.urljoin(self.openshift_api, "namespaces/")
            url = urlparse.urljoin(url, "%s/" % namespace)
            url = urlparse.urljoin(url, "deploymentconfigs/")
        elif kind == "Route":
            url = urlparse.urljoin(self.openshift_api, "namespaces/")
            url = urlparse.urljoin(url, "%s/" % namespace)
            url = urlparse.urljoin(url, "routes/")
        elif kind == "Template":
            url = urlparse.urljoin(self.openshift_api, "namespaces/")
            url = urlparse.urljoin(url, "%s/" % namespace)
            url = urlparse.urljoin(url, "templates/")
        elif kind == "Service":
            url = urlparse.urljoin(self.kubernetes_api, "namespaces/")
            url = urlparse.urljoin(url, "%s/" % namespace)
            url = urlparse.urljoin(url, "services/")
        elif kind == "Pod":
            url = urlparse.urljoin(self.kubernetes_api, "namespaces/")
            url = urlparse.urljoin(url, "%s/" % namespace)
            url = urlparse.urljoin(url, "pods/")
        elif kind == "Persistentvolumeclaim":
            url = urlparse.urljoin(self.kubernetes_api, "namespaces/")
            url = urlparse.urljoin(url, "%s/" % namespace)
            url = urlparse.urljoin(url, "persistentvolumeclaims/")
        else:
            logger.error("UNKNOWN kind %s", kind)

        if name:
            url = urlparse.urljoin(url, name)

        url = urlparse.urljoin(url, "?access_token={}".format(self.access_token))
        logger.debug("url: %s", url)
        return url
