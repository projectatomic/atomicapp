import mock
import unittest
from atomicapp.nulecule.base import NuleculeComponent


class TestNuleculeComponentLoadArtifactPathsForPath(unittest.TestCase):
    """Test loading artifacts from an artifact path"""

    @mock.patch('atomicapp.nulecule.base.os.path.isfile')
    def test_file_path(self, mock_os_path_isfile):
        nc = NuleculeComponent('some-name', 'some/path')
        mock_os_path_isfile.return_value = True
        self.assertEqual(
            nc._get_artifact_paths_for_path('some/path/to/file'),
            ['some/path/to/file'])

    @mock.patch('atomicapp.nulecule.base.os.listdir')
    @mock.patch('atomicapp.nulecule.base.os.path.isdir')
    @mock.patch('atomicapp.nulecule.base.os.path.isfile')
    def test_dir_path(self, mock_os_path_isfile, mock_os_path_isdir,
                      mock_os_listdir):
        nc = NuleculeComponent('some-name', 'some/path')
        mock_os_path_isfile.return_value = False
        mock_os_path_isdir.side_effect = lambda path: True if path.endswith('dir') else False
        mock_os_listdir.return_value = [
            '.foo',
            'some-dir',
            'file1',
            'file2'
        ]
        self.assertEqual(
            nc._get_artifact_paths_for_path('artifacts-dir'),
            ['artifacts-dir/file1', 'artifacts-dir/file2'])


class TestNuleculeComponentLoad(unittest.TestCase):

    @mock.patch('atomicapp.nulecule.base.NuleculeComponent.load_external_application')
    def test_load_without_nodeps(self, mock_load_external_application):
        nc = NuleculeComponent('some-name', 'some/path', source='blah')
        dryrun = False
        nc.load(False, dryrun)
        mock_load_external_application.assert_called_once_with(dryrun)

    @mock.patch(
        'atomicapp.nulecule.base.NuleculeComponent.load_external_application')
    def test_load_with_nodeps(self, mock_load_external_application):
        nc = NuleculeComponent('some-name', 'some/path', source='blah')
        dryrun = False
        nc.load(True, dryrun)
        self.assertEqual(mock_load_external_application.call_count, 0)
