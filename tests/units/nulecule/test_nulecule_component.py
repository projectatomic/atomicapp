import copy
import mock
import unittest
from atomicapp.nulecule.base import NuleculeComponent, Nulecule


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


class TestNuleculeComponentRun(unittest.TestCase):
    """Test Nulecule component run"""

    def test_run_external_app(self):
        nc = NuleculeComponent('some-name', 'some/path')
        mock_nulecule = mock.Mock(name='nulecule')
        nc._app = mock_nulecule
        dryrun = False

        nc.run('some-provider', dryrun)
        mock_nulecule.run.assert_called_once_with('some-provider', dryrun)

    @mock.patch('atomicapp.nulecule.base.NuleculeComponent.get_provider')
    def test_run_local_artifacts(self, mock_get_provider):
        nc = NuleculeComponent('some-name', 'some/path')
        nc.rendered_artifacts = {'some-provider-x': ['a', 'b', 'c']}
        dryrun = False
        provider_key = 'some-provider'
        mock_provider = mock.Mock(name='provider')
        mock_get_provider.return_value = ('some-provider-x', mock_provider)

        nc.run(provider_key, dryrun)
        mock_get_provider.assert_called_once_with(provider_key, dryrun)
        self.assertEqual(mock_provider.artifacts, ['a', 'b', 'c'])
        mock_provider.init.assert_called_once_with()
        mock_provider.deploy.assert_called_once_with()


class TestNuleculeComponentStop(unittest.TestCase):
    """Test Nulecule component stop"""

    def test_stop_external_app(self):
        """Test stopping an external application"""
        nc = NuleculeComponent('some-name', 'some/path')
        mock_nulecule = mock.Mock(name='nulecule')
        nc._app = mock_nulecule
        dryrun = False

        nc.stop('some-provider', dryrun)
        mock_nulecule.stop.assert_called_once_with('some-provider', dryrun)

    @mock.patch('atomicapp.nulecule.base.NuleculeComponent.get_provider')
    def test_stop_local_app(self, mock_get_provider):
        """Test stopping a local application"""
        nc = NuleculeComponent('some-name', 'some/path')
        nc.rendered_artifacts = {'some-provider-x': ['a', 'b', 'c']}
        dryrun = False
        provider_key = 'some-provider'
        mock_provider = mock.Mock(name='provider')
        mock_get_provider.return_value = ('some-provider-x', mock_provider)

        nc.stop(provider_key, dryrun)
        mock_get_provider.assert_called_once_with(provider_key, dryrun)
        self.assertEqual(mock_provider.artifacts, ['a', 'b', 'c'])
        mock_provider.init.assert_called_once_with()
        mock_provider.undeploy.assert_called_once_with()


class TestNuleculeComponentLoadConfig(unittest.TestCase):
    """Test loading config for a Nulecule component"""

    def test_load_config_local_app(self):
        """Test load config for local app"""
        params = [
            {'name': 'key1'},
            {'name': 'key2'}
        ]
        nc = NuleculeComponent('some-app', 'some/path', params=params)
        initial_config = {
            'general': {'a': 'b', 'key2': 'val2'},
            'some-app': {'key1': 'val1'}
        }
        nc.load_config(config=copy.deepcopy(initial_config))
        self.assertEqual(nc.config, {
            'general': {'a': 'b', 'key2': 'val2'},
            'some-app': {'key1': 'val1', 'key2': 'val2'}
        })

    @mock.patch('atomicapp.nulecule.base.NuleculeComponent.merge_config')
    def test_load_config_external_app(self, mock_merge_config):
        """Test load config for external app"""
        params = [
            {'name': 'key1'},
            {'name': 'key2'}
        ]
        nc = NuleculeComponent('some-app', 'some/path', params=params)
        mock_nulecule = mock.Mock(
            name='nulecule',
            spec=Nulecule('some-id', '0.0.2', {}, [], 'some/path')
        )
        nc._app = mock_nulecule
        initial_config = {
            'general': {'a': 'b', 'key2': 'val2'},
            'some-app': {'key1': 'val1'}
        }
        nc.load_config(config=copy.deepcopy(initial_config))
        mock_nulecule.load_config.assert_called_once_with(
            config={
                'general': {'a': 'b', 'key2': 'val2'},
                'some-app': {'key1': 'val1', 'key2': 'val2'}
            }, ask=False, skip_asking=False)
        mock_merge_config.assert_called_once_with(
            nc.config, mock_nulecule.config)


class TestNuleculeComponentLoadExternalApplication(unittest.TestCase):
    """
    Test loading an external Nulecule application from a Nulecule
    component.
    """

    @mock.patch('atomicapp.nulecule.base.Nulecule')
    @mock.patch('atomicapp.nulecule.base.os.path.isdir')
    def test_loading_existing_app(self, mock_os_path_isdir, mock_Nulecule):
        nc = NuleculeComponent('some-app', 'some/path')
        dryrun, update = False, False
        mock_os_path_isdir.return_value = True

        nc.load_external_application(dryrun=dryrun, update=update)
        expected_external_app_path = 'some/path/external/some-app'
        mock_os_path_isdir.assert_called_once_with(
            expected_external_app_path)
        mock_Nulecule.load_from_path.assert_called_once_with(
            expected_external_app_path, dryrun=dryrun, update=update)

    @mock.patch('atomicapp.nulecule.base.Nulecule')
    @mock.patch('atomicapp.nulecule.base.os.path.isdir')
    def test_loading_app_by_unpacking(self, mock_os_path_isdir,
                                      mock_Nulecule):
        nc = NuleculeComponent('some-app', 'some/path')
        dryrun, update = False, False
        mock_os_path_isdir.return_value = False

        nc.load_external_application(dryrun=dryrun, update=update)
        expected_external_app_path = 'some/path/external/some-app'
        mock_os_path_isdir.assert_called_once_with(
            expected_external_app_path)
        mock_Nulecule.unpack.assert_called_once_with(
            nc.source, expected_external_app_path,
            namespace=nc.namespace, dryrun=dryrun, update=update)
