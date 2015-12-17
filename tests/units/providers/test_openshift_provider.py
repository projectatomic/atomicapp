# -*- coding: utf-8 -*-
import unittest
import mock
from atomicapp.providers.openshift import OpenShiftProvider


class OpenshiftProviderTestMixin(object):

    def setUp(self):
        self.patcher = mock.patch('atomicapp.providers.openshift.OpenshiftClient')
        self.mock_OpenshiftClient = self.patcher.start()
        self.mock_oc = self.mock_OpenshiftClient()

    def get_oc_provider(self, dryrun=False, artifacts=[]):
        op = OpenShiftProvider({}, '.', dryrun)
        op.artifacts = artifacts
        op.init()
        return op

    def tearDown(self):
        self.patcher.stop()


class TestOpenshiftProviderDeploy(OpenshiftProviderTestMixin, unittest.TestCase,):

    def test_deploy(self):
        op = self.get_oc_provider()
        op.oapi_resources = ['foo']
        op.openshift_artifacts = {
            'pods': [
                {
                    'metadata': {
                        'namespace': 'foo'
                    }
                }
            ]
        }

        op.deploy()

        self.mock_oc.deploy.assert_called_once_with(
            'namespaces/foo/pods/?access_token=None',
            op.openshift_artifacts['pods'][0])

    def test_deploy_dryrun(self):
        op = self.get_oc_provider(dryrun=True)
        op.oapi_resources = ['foo']
        op.openshift_artifacts = {
            'pods': [
                {
                    'metadata': {
                        'namespace': 'foo'
                    }
                }
            ]
        }

        op.deploy()

        self.assertFalse(self.mock_oc.deploy.call_count)


class TestOpenshiftProviderProcessArtifacts(unittest.TestCase):
    pass


class TestOpenshiftProviderProcessTemplate(unittest.TestCase):
    pass
