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

import unittest
import mock
import tempfile
import os
import json
from atomicapp.plugin import Plugin, ProviderFailedException
from atomicapp.nulecule_base import Nulecule_Base
from atomicapp.providers.kubernetes import KubernetesProvider

MOCK_CONTENT = "mock_provider_call_content"

def mock_provider_call(self, cmd):
    return MOCK_CONTENT

class TestKubernetesProviderBase(unittest.TestCase):
    def setUp(self):
        self.nulecule_base = Nulecule_Base(dryrun = True)
        self.tmpdir = tempfile.mkdtemp(prefix = "atomicapp-test", dir = "/tmp")
        self.plugin = Plugin()
        self.plugin.load_plugins()

    def tearDown(self):
        pass

    def create_temp_file(self):
        return tempfile.mktemp(prefix = "test-config", dir = self.tmpdir)

    def prepare_provider(self, data):
        self.nulecule_base.loadAnswers(data)
        provider_class = self.plugin.getProvider(self.nulecule_base.provider)
        config = self.nulecule_base.getValues(skip_asking=True)
        provider = provider_class(config, self.tmpdir, dryrun = False)

        return provider

    @mock.patch.object(KubernetesProvider, '_call', mock_provider_call)
    def test_provider_config_exist(self):
        provider_config_path = self.create_temp_file()
        mock_content = "%s_%s" % (MOCK_CONTENT, "_unchanged")
        with open(provider_config_path, "w") as fp:
            fp.write(mock_content)

        data = {'general': {'namespace': 'testing', 'provider': 'kubernetes', 'providerconfig': provider_config_path}}
        
        provider = self.prepare_provider(data)

        self.assertEqual(provider.config_file, provider_config_path)
        provider.checkConfigFile()
        with open(provider_config_path, "r") as fp:
            self.assertEqual(fp.read(), mock_content)

    @mock.patch("kubernetes.KubernetesProvider._call", mock_provider_call)
    def test_provider_check_config_generation(self):
        path = self.create_temp_file()
        data = {'general': {'namespace': 'testing', 'provider': 'kubernetes', 'providerconfig': path}}

        provider = self.prepare_provider(data)

        provider.checkConfigFile()
        with open(path, "r") as fp:
            self.assertEqual(fp.read(), MOCK_CONTENT)

    def test_provider_check_config_fail(self):
        path = self.create_temp_file()
        data = {'general': {'namespace': 'testing', 'provider': 'openshift'}}

        provider = self.prepare_provider(data)

        self.assertRaises(ProviderFailedException, provider.checkConfigFile)
