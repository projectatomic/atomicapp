import unittest
from atomicapp.nulecule_base import Nulecule_Base

class TestNuleculeBase(unittest.TestCase):

    def setUp(self):
        self.nulecule_base = Nulecule_Base(
            dryrun=True,
            cli_provider="kubernetes")

    def tearDown(self):
        pass

    def test_answers_config(self):
        data = {'general': {'namespace': 'testing', 'provider': 'kubernetes'}}
        self.nulecule_base.loadAnswers(data)
        config = self.nulecule_base.getValues()
        self.assertEqual(config["namespace"], "testing")

    def test_answers_config_with_skip(self):
        data = {'general': {'namespace': 'testing', 'provider': 'kubernetes'}}
        self.nulecule_base.loadAnswers(data)
        config = self.nulecule_base.getValues(skip_asking=True)
        self.assertEqual(config["namespace"], "testing")
