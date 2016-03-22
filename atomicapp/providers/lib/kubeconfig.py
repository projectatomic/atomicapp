import anymarkup

from atomicapp.plugin import ProviderFailedException
from atomicapp.constants import (ACCESS_TOKEN_KEY,
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

        context = None
        for co in kubecfg["contexts"]:
            if co["name"] == current_context:
                context = co

        if not context:
            raise ProviderFailedException()

        cluster = None
        for cl in kubecfg["clusters"]:
            if cl["name"] == context["context"]["cluster"]:
                cluster = cl

        user = None
        for usr in kubecfg["users"]:
            if usr["name"] == context["context"]["user"]:
                user = usr

        if not cluster or not user:
            raise ProviderFailedException()

        logger.debug("context: %s", context)
        logger.debug("cluster: %s", cluster)
        logger.debug("user: %s", user)

        url = cluster["cluster"]["server"]
        token = user["user"]["token"]
        if "namespace" in context["context"]:
            namespace = context["context"]["namespace"]
        if "insecure-skip-tls-verify" in cluster["cluster"]:
            tls_verify = not cluster["cluster"]["insecure-skip-tls-verify"]
        elif "certificate-authority" in cluster["cluster"]:
            ca = cluster["cluster"]["certificate-authority"]

        return {PROVIDER_API_KEY: url,
                ACCESS_TOKEN_KEY: token,
                NAMESPACE_KEY: namespace,
                PROVIDER_TLS_VERIFY_KEY: tls_verify,
                PROVIDER_CA_KEY: ca}
