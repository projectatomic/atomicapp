import unittest
import mock
import tempfile
import os
import json
from atomicapp.plugin import Plugin, ProviderFailedException
from atomicapp.nulecule_base import Nulecule_Base

class TestNuleculeBase(unittest.TestCase):
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

    def test_provider_config_exist(self):
        provider_config_path = self.create_temp_file()
        with open(provider_config_path, "w") as fp:
            fp.write("This is config")

        data = {'general': {'namespace': 'testing', 'provider': 'kubernetes', 'providerconfig': '%s' % provider_config_path}}
        
        provider = self.prepare_provider(data)

        self.assertEqual(provider.config_file, provider_config_path)

    def test_provider_check_config_fail(self):
        data = {'general': {'namespace': 'testing', 'provider': 'kubernetes'}}

        provider = self.prepare_provider(data)

        self.assertRaises(ProviderFailedException, provider.checkConfigFile)
