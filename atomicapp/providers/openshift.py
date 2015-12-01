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

import os
import anymarkup
import requests
from urlparse import urljoin
from atomicapp.plugin import Provider, ProviderFailedException
from atomicapp.constants import (PROVIDER_API_KEY, ACCESS_TOKEN_KEY,
                                 DEFAULT_NAMESPACE, NAMESPACE_KEY)

import logging
logger = logging.getLogger(__name__)


class OpenShiftProvider(Provider):
    key = "openshift"
    cli_str = "oc"
    cli = None
    config_file = None
    template_data = None
    providerapi = "https://127.0.0.1:8443"
    openshift_api = None
    kubernetes_api = None
    access_token = None
    namespace = DEFAULT_NAMESPACE

    # Parsed artifacts. Key is kind of artifacts. Value is list of artifacts.
    openshift_artifacts = {}

    def init(self):
        self.openshift_artifacts = {}

        if self.config.get(ACCESS_TOKEN_KEY):
            self.access_token = self.config.get(ACCESS_TOKEN_KEY)
        else:
            raise ProviderFailedException("No %s specified" % ACCESS_TOKEN_KEY)

        if self.config.get(PROVIDER_API_KEY):
            self.providerapi = self.config.get(PROVIDER_API_KEY)

        if self.config.get(NAMESPACE_KEY):
            self.namespace = self.config.get(NAMESPACE_KEY)

        # construct full urls for api endpoints
        self.openshift_api = urljoin(self.providerapi, "oapi/v1/")
        self.kubernetes_api = urljoin(self.providerapi, "api/v1/")

        logger.debug("openshift_api = %s", self.openshift_api)
        logger.debug("kubernetes_api = %s", self.kubernetes_api)

        self._process_artifacts()

    def _get_namespace(self, artifact):
        """ return artifacts namespace

        if specified use namespace from artificaft else return self.namespace
        """
        if "metadata" in artifact and "namespace" in artifact["metadata"]:
            return artifact["metadata"]["namespace"]
        return self.namespace

    def deploy(self):
        logger.debug("starting deploy")
        # TODO: remove running components if one component fails issue:#428
        for kind, objects in self.openshift_artifacts.iteritems():
            for artifact in objects:
                namespace = self._get_namespace(artifact)
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
        # TODO: scale down replicationController before deleting deploymentConfig
        for kind, objects in self.openshift_artifacts.iteritems():
            for artifact in objects:
                namespace = self._get_namespace(artifact)

                # get name from metadata so we know which object sould be deleted
                if "metadata" in artifact and \
                        "name" in artifact["metadata"]:
                    name = artifact["metadata"]["name"]
                else:
                    raise ProviderFailedException("Cannot undeploy. There is no"
                                                  " name in artifacts metadata "
                                                  "artifact=%s" % artifact)

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
                data = anymarkup.parse(fp)
                # kind has to be specified in artifact
                if "kind" not in data.keys():
                    raise ProviderFailedException(
                        "Error processing %s artifact. There is no kind" %
                        artifact)
                kind = data['kind'].title()
                # add parsed artifact to dict
                if kind not in self.openshift_artifacts.keys():
                    self.openshift_artifacts[kind] = []
                self.openshift_artifacts[kind].append(data)

    def _get_url(self, namespace, kind, name=None):
        """ return url for given kind

        return either openshift or kubernetes url depending on what kind is passed
        """
        url = None

        # TODO: this is ugly :-(
        if kind == "Deploymentconfig":
            url = urljoin(self.openshift_api, "namespaces/")
            url = urljoin(url, "%s/" % namespace)
            url = urljoin(url, "deploymentconfigs/")
        elif kind == "Route":
            url = urljoin(self.openshift_api, "namespaces/")
            url = urljoin(url, "%s/" % namespace)
            url = urljoin(url, "routes/")
        elif kind == "Template":
            url = urljoin(self.openshift_api, "namespaces/")
            url = urljoin(url, "%s/" % namespace)
            url = urljoin(url, "templates/")
        elif kind == "Service":
            url = urljoin(self.kubernetes_api, "namespaces/")
            url = urljoin(url, "%s/" % namespace)
            url = urljoin(url, "services/")
        elif kind == "Pod":
            url = urljoin(self.kubernetes_api, "namespaces/")
            url = urljoin(url, "%s/" % namespace)
            url = urljoin(url, "pods/")
        elif kind == "Persistentvolumeclaim":
            url = urljoin(self.kubernetes_api, "namespaces/")
            url = urljoin(url, "%s/" % namespace)
            url = urljoin(url, "persistentvolumeclaims/")
        else:
            logger.error("UNKNOWN kind %s", kind)

        if name:
            url = urljoin(url, name)

        url = urljoin(url, "?access_token={}".format(self.access_token))
        logger.debug("url: %s", url)
        return url
