import mock
import unittest

from atomicapp.plugin import Plugin
 
class TestPluginGetProvider(unittest.TestCase):
 
    """Test Plugin getProvider"""
    def test_getProvider(self):
        """
        Test if getProvider is returning appropriate classes to the
        corresponding keys.
        """
        p = Plugin()
       
        docker_mock = mock.Mock()
        kubernetes_mock = mock.Mock()
        # keep some mock objects in place of the actual corresponding
        # classes, getProvider reads from `plugins` dict.
        p.plugins = {
            'docker': docker_mock,
            'kubernetes': kubernetes_mock,
        }
        self.assertEqual(p.getProvider('docker'), docker_mock)
        self.assertEqual(p.getProvider('kubernetes'), kubernetes_mock)
        # if non-existent key provided
        self.assertEqual(p.getProvider('some_random'), None)
