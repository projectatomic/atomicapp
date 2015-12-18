# -*- coding: utf-8 -*-
import unittest
import mock
from atomicapp.providers.openshift import OpenShiftProvider
from atomicapp.plugin import ProviderFailedException


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


class TestOpenshiftProviderProcessArtifactData(OpenshiftProviderTestMixin, unittest.TestCase):

    def test_process_artifact_data_non_template_kind(self):
        artifact_data = {
            'kind': 'Pod',
            'pods': [
                {
                    'metadata': {
                        'namespace': 'foo'
                    }
                }
            ]
        }
        self.mock_oc.get_oapi_resources.return_value = ['pods']

        op = self.get_oc_provider()

        op._process_artifact_data('foo', artifact_data)

        self.assertEqual(op.openshift_artifacts,
                         {'pod': [artifact_data]})

    def test_process_artifact_data_template_kind(self):
        artifact_data = {
            'kind': 'Template',
            'objects': [
                {
                    'kind': 'Pod',
                    'metadata': {
                        'namespace': 'foo'
                    }
                },
                {
                    'kind': 'Service',
                    'metadata': {
                        'namespace': 'foo'
                    }
                }
            ]
        }
        self.mock_oc.get_oapi_resources.return_value = ['templates']
        op = self.get_oc_provider()
        self.mock_oc.process_template.return_value = artifact_data['objects']

        op._process_artifact_data('foo', artifact_data)

        self.assertEqual(
            op.openshift_artifacts, {
                'pod': [
                    {'kind': 'Pod', 'metadata': {'namespace': 'foo'}}
                ],
                'service': [
                    {'kind': 'Service', 'metadata': {'namespace': 'foo'}}
                ]
            }
        )

    def test_process_artifact_data_error_resource_not_in_resources(self):
        artifact_data = {
            'kind': 'foobar'
        }

        op = self.get_oc_provider()

        self.assertRaises(
            ProviderFailedException,
            op._process_artifact_data, 'foo', artifact_data)

    def test_process_artifact_data_error_kind_key_missing(self):
        artifact_data = {}
        op = self.get_oc_provider()

        self.assertRaises(
            ProviderFailedException,
            op._process_artifact_data, 'foo', artifact_data)


class TestOpenshiftProviderParseKubeconfData(OpenshiftProviderTestMixin, unittest.TestCase):

    def test_parse_kubeconf_data(self):
        kubecfg_data = {
            'current-context': 'context2',
            'contexts': [
                {
                    'name': 'context1',
                },
                {
                    'name': 'context2',
                    'context': {
                        'cluster': 'cluster1',
                        'user': 'user1',
                        'namespace': 'namespace1'
                    }
                }
            ],
            'clusters': [
                {
                    'name': 'cluster1',
                    'cluster': {
                        'server': 'server1'
                    }
                }
            ],
            'users': [
                {
                    'name': 'user1',
                    'user': {
                        'token': 'token1'
                    }
                }
            ]
        }

        op = self.get_oc_provider()
        self.assertEqual(op._parse_kubeconf_data(kubecfg_data),
                         ('server1', 'token1', 'namespace1'))

    def test_parse_kubeconf_data_no_context(self):
        kubecfg_data = {
            'current-context': 'context2',
            'contexts': [
                {
                    'name': 'context1',
                }
            ],
            'clusters': [
                {
                    'name': 'cluster1',
                    'cluster': {
                        'server': 'server1'
                    }
                }
            ],
            'users': [
                {
                    'name': 'user1',
                    'user': {
                        'token': 'token1'
                    }
                }
            ]
        }

        op = self.get_oc_provider()
        self.assertRaises(ProviderFailedException,
                          op._parse_kubeconf_data, kubecfg_data)

    def test_parse_kubeconf_data_no_user(self):
        kubecfg_data = {
            'current-context': 'context2',
            'contexts': [
                {
                    'name': 'context1',
                },
                {
                    'name': 'context2',
                    'context': {
                        'cluster': 'cluster1',
                        'user': 'user1',
                        'namespace': 'namespace1'
                    }
                }
            ],
            'clusters': [
                {
                    'name': 'cluster1',
                    'cluster': {
                        'server': 'server1'
                    }
                }
            ],
            'users': [
            ]
        }

        op = self.get_oc_provider()
        self.assertRaises(ProviderFailedException,
                          op._parse_kubeconf_data, kubecfg_data)
