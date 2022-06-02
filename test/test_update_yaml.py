import os
from unittest import TestCase

import yaml
from kazoo.client import KazooClient

from zkyaml.clients.zkconfig import ZKConfig

ROOT_TEST_DIRECTORY = os.path.dirname(__file__)

def get_full_path(*path_from_tests_base_directory):
    return os.path.join(ROOT_TEST_DIRECTORY, *path_from_tests_base_directory)

import zkyaml.common.env_variables as envv
envv.default_repo_path = get_full_path('data')

import zkyaml.update.update_config_service as ucs


class TestUpdateConfigService(TestCase):
    def setUp(self):
        self._file_name = get_full_path('data/vc/production/test.yaml')
        self._update_config_service = ucs.UpdateConfigService('127.0.0.1')
        self._zk = KazooClient('127.0.0.1')
        self._zk.start()
        self._context = 'staging'
        self._path = self._update_config_service.get_path(self._context)

    def tearDown(self):
        self._zk.stop()

    def test_raw(self):
        file_name = self._file_name
        self._update_config_service.update_context(self._context, [file_name, file_name])
        yaml_str, stat = self._zk.get(path=self._update_config_service.get_path(self._context))
        with open(file_name, 'r') as f:
            data = f.read()
        self.assertEqual(yaml.load(data, yaml.FullLoader), yaml.load(yaml_str, yaml.FullLoader))


    def test_with_file_selection(self):
        file_name = self._file_name
        self._update_from_files()
        yaml_str, stat = self._zk.get(path=self._update_config_service.get_path(self._context))
        with open(file_name, 'r') as f:
            data = f.read()
        self.assertEqual(yaml.load(data, yaml.FullLoader), yaml.load(yaml_str, yaml.FullLoader))

    def test_client(self):
        self._update_from_files()
        client = ZKConfig(hosts='127.0.0.1', context_list=['vc_yaml/global', 'vc_yaml/staging'])
        config = client.get_config()
        self.assertTrue(config['entry_from_global'])
        self.assertTrue(config['entry_from_staging'])
        self.assertEqual(config['should_be_one_in_staging'], 1)

    def _update_from_files(self):
        class UService(ucs.UpdateConfigService):
            def _resolve_pull_output(self):
                return """
                    vc/production/test.yaml
                    vc/staging/test.yaml
                    vc/global.yaml
                """

            def _changed(self):
                return True

        update_config_service = UService('127.0.0.1')
        update_config_service.update()

