import anymarkup

from atomicapp.plugin import ProviderFailedException
from atomicapp.constants import (PROVIDER_AUTH_KEY,
                                 LOGGER_DEFAULT,
                                 NAMESPACE_KEY,
                                 PROVIDER_API_KEY,
                                 PROVIDER_TLS_VERIFY_KEY,
                                 PROVIDER_CA_KEY)
import logging
logger = logging.getLogger(LOGGER_DEFAULT)


class KubeConfig(object):

    @staticmethod
    def parse_kubeconf(filename):
        """"
        Parse kubectl config file

        Args:
            filename (string): path to configuration file (e.g. ./kube/config)

        Returns:
            dict of parsed values from config

        Example of expected file format:
            apiVersion: v1
            clusters:
            - cluster:
                server: https://10.1.2.2:8443
                certificate-authority: path-to-ca.cert
                insecure-skip-tls-verify: false
              name: 10-1-2-2:8443
            contexts:
            - context:
                cluster: 10-1-2-2:8443
                namespace: test
                user: test-admin/10-1-2-2:8443
              name: test/10-1-2-2:8443/test-admin
            current-context: test/10-1-2-2:8443/test-admin
            kind: Config
            preferences: {}
            users:
            - name: test-admin/10-1-2-2:8443
            user:
                token: abcdefghijklmnopqrstuvwxyz0123456789ABCDEF
        """
        logger.debug("Parsing %s", filename)

        with open(filename, 'r') as fp:
            kubecfg = anymarkup.parse(fp.read())

        try:
            return KubeConfig.parse_kubeconf_data(kubecfg)
        except ProviderFailedException:
            raise ProviderFailedException('Invalid %s' % filename)

    @staticmethod
    def parse_kubeconf_data(kubecfg):
        """
        Parse kubeconf data.

        Args:
            kubecfg (dict): Kubernetes config data

        Returns:
            dict of parsed values from config
        """
        url = None
        token = None
        namespace = None
        tls_verify = True
        ca = None

        current_context = kubecfg["current-context"]

        logger.debug("current context: %s", current_context)

        try:
            context = filter(lambda co: co["name"] == current_context,
                             kubecfg["contexts"])[0]
            logger.debug("context: %s", context)

            cluster = filter(lambda cl: cl["name"] == context["context"]["cluster"],
                             kubecfg["clusters"])[0]
            logger.debug("cluster: %s", cluster)

            user = filter(lambda usr: usr["name"] == context["context"]["user"],
                          kubecfg["users"])[0]
            logger.debug("user: %s", user)
        except IndexError:
            raise ProviderFailedException()

        url = cluster["cluster"]["server"]
        token = user["user"]["token"]
        if "namespace" in context["context"]:
            namespace = context["context"]["namespace"]
        if "insecure-skip-tls-verify" in cluster["cluster"]:
            tls_verify = not cluster["cluster"]["insecure-skip-tls-verify"]
        elif "certificate-authority" in cluster["cluster"]:
            ca = cluster["cluster"]["certificate-authority"]

        return {PROVIDER_API_KEY: url,
                PROVIDER_AUTH_KEY: token,
                NAMESPACE_KEY: namespace,
                PROVIDER_TLS_VERIFY_KEY: tls_verify,
                PROVIDER_CA_KEY: ca}
