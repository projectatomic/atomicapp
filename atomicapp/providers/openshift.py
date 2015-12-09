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
from atomicapp.constants import (PROVIDER_API_KEY,
                                 ACCESS_TOKEN_KEY,
                                 DEFAULT_NAMESPACE,
                                 NAMESPACE_KEY)

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
    ssl_verify = False

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

        # get list of supported resources for each api
        self.oapi_resources = requests.get(
            self.openshift_api, verify=self.ssl_verify).json()["resources"]
        self.kapi_resources = requests.get(
            self.kubernetes_api, verify=self.ssl_verify).json()["resources"]

        # convert resources list of dicts to list of names
        self.oapi_resources = [res['name'] for res in self.oapi_resources]
        self.kapi_resources = [res['name'] for res in self.kapi_resources]

        logger.debug("Openshift resources %s", self.oapi_resources)
        logger.debug("Kubernetes resources %s", self.kapi_resources)

        self._process_artifacts()

    def _get_namespace(self, artifact):
        """
        Return namespace for artifact. If namespace is specified inside
        artifact use that, if not return default namespace (as specfied in
        answers.conf)

        Args:
            artifact (dict): OpenShift/Kubernetes object

        Returns:
            namespace (str)
        """
        if "metadata" in artifact and "namespace" in artifact["metadata"]:
            return artifact["metadata"]["namespace"]
        return self.namespace

    def deploy(self):
        logger.debug("Deploying to OpenShift")
        # TODO: remove running components if one component fails issue:#428
        for kind, objects in self.openshift_artifacts.iteritems():
            for artifact in objects:
                namespace = self._get_namespace(artifact)
                url = self._get_url(namespace, kind)

                if self.dryrun:
                    logger.info("DRY-RUN: %s", url)
                    continue
                res = requests.post(url, json=artifact, verify=self.ssl_verify)
                if res.status_code == 201:
                    logger.info("Object %s sucessfully deployed.",
                                artifact['metadata']['name'])
                else:
                    msg = "%s %s" % (res.status_code, res.content)
                    logger.error(msg)
                    # TODO: remove running components (issue: #428)
                    raise ProviderFailedException(msg)

    def undeploy(self):
        logger.debug("starting undeploy")
        # TODO: scale down replicationController before deleting deploymentConf
        for kind, objects in self.openshift_artifacts.iteritems():
            for artifact in objects:
                namespace = self._get_namespace(artifact)

                # get name from metadata so we know which object to be deleted
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

                res = requests.delete(url, verify=self.ssl_verify)
                if res.status_code == 200:
                    logger.info(" %s sucessfully undeployed.", res.content)
                else:
                    msg = "%s %s" % (res.status_code, res.content)
                    logger.error(msg)
                    raise ProviderFailedException(msg)

    def _process_artifacts(self):
        """
        Parse OpenShift manifests files and checks if manifest under
        process is valid. Reads self.artifacts and saves parsed artifacts
        to self.openshift_artifacts
        """
        for artifact in self.artifacts:
            logger.debug("Processing artifact: %s", artifact)
            data = None
            with open(os.path.join(self.path, artifact), "r") as fp:
                data = anymarkup.parse(fp, force_types=None)
            # kind has to be specified in artifact
            if "kind" not in data.keys():
                raise ProviderFailedException(
                    "Error processing %s artifact. There is no kind" %
                    artifact)

            kind = data["kind"].lower()

            # process templates
            if kind == "template":
                processed_objects = self._process_template(data)
                # add all processed object to artifacts dict
                for obj in processed_objects:
                    obj_kind = obj["kind"].lower()
                    if obj_kind not in self.openshift_artifacts.keys():
                        self.openshift_artifacts[obj_kind] = []
                    self.openshift_artifacts[obj_kind].append(obj)
                continue

            # add parsed artifact to dict
            if kind not in self.openshift_artifacts.keys():
                self.openshift_artifacts[kind] = []
            self.openshift_artifacts[kind].append(data)

    def _process_template(self, template):
        """
        Call OpenShift api and process template.
        Templates allow parameterization of resources prior to being sent to
        the server for creation or update. Templates have "parameters",
        which may either be generated on creation or set by the user.

        Args:
            template (dict): template to process

        Returns:
            List of objects from processed template.
        """
        logger.debug("processing template: %s", template)
        url = self._get_url(self._get_namespace(template), 'processedtemplates')
        res = requests.post(url, json=template, verify=self.ssl_verify)
        if res.status_code == 201:
            logger.info("template proccessed %s", template['metadata']['name'])
            logger.debug("processed template %s", res.json())
            return res.json()['objects']
        else:
            msg = "%s %s" % (res.status_code, res.content)
            logger.error(msg)
            raise ProviderFailedException(msg)

    def _kind_to_resource(self, kind):
        """
        Converts kind to resource name. It is same logics
        as in k8s.io/kubernetes/pkg/api/meta/restmapper.go (func KindToResource)
        Example:
            Pod -> pods
            Policy - > policies
            BuildConfig - > buildconfigs

        Args:
            kind (str): Kind of the object

        Returns:
            Resource name (str) (kind in plural form)
        """
        singular = kind.lower()
        if singular.endswith("status"):
            plural = singular + "es"
        else:
            if singular[-1] == "s":
                plural = singular
            elif singular[-1] == "y":
                plural = singular.rstrip("y") + "ies"
            else:
                plural = singular + "s"
        return plural

    def _get_url(self, namespace, kind, name=None):
        """
        Some kinds/resources are managed by OpensShift and some by Kubernetes.
        Here we compose right url (Kubernets or OpenShift) for given kind.
        If resource is managed by Kubernetes or OpenShift is determined by
        self.kapi_resources/self.oapi_resources lists
        Example:
            For namespace=project1, kind=DeploymentConfig, name=dc1 result
            would be http://example.com:8443/oapi/v1/namespaces/project1/deploymentconfigs/dc1

        Args:
            namespace (str): Kubernetes namespace or Openshift project name
            kind (str): kind of the object
            name (str): object name if modifying or deleting specific object (optional)

        Returns:
            Full url (str) for given kind, namespace and name
        """
        url = None

        resource = self._kind_to_resource(kind)

        if resource in self.oapi_resources:
            url = self.openshift_api
        elif resource in self.kapi_resources:
            url = self.kubernetes_api
        else:
            msg = "Unsupported resource %s" % resource
            logger.error(msg)
            raise ProviderFailedException(msg)

        url = urljoin(url, "namespaces/%s/%s/" % (namespace, resource))

        if name:
            url = urljoin(url, name)

        url = urljoin(url, "?access_token={}".format(self.access_token))
        logger.debug("url: %s", url)
        return url
