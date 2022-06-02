#!/usr/bin/python
import os
import re
import yaml
import subprocess as sp
from kazoo.client import KazooClient


import zkyaml.update.update_service_base as usb

from zkyaml.common import logger
from zkyaml.common.env_variables import default_base_path, default_repo_path, default_repo_files_path


class UpdateConfigService(usb.UpdateGitServiceBase):
    def __init__(self, hosts):
        super(UpdateConfigService, self).__init__()
        self._hosts = hosts
        self._base_path = default_base_path
        self._logger = logger
        self._repo_path = default_repo_path
        self._repo_files_path = default_repo_files_path
        self._full_base_path = os.path.join(self._repo_path, default_repo_files_path)

    def update_config(self):
        self.update()

    # Implements abstractmethod
    def _get_path_to_repository(self):
        return self._repo_path

    # Implements abstractmethod
    def _get_branch_name(self):
        return 'master'

    # Implements abstractmethod
    def _update(self):
        pull_output = self._resolve_pull_output()
        context_files = self._collect_files_and_context(pull_output)
        if not context_files:
            self._logger.warning('changes were not in context files')
            return True

        ret_val = True
        for context, file_list in context_files.items():
            try:
                self.update_context(context, file_list)
                self._logger.info('updated zookeeper for context: %s' % context)
            except:
                self._logger.exception('updating zookeeper for context %s FAILED' % context)
                ret_val = False

        return ret_val

    def _resolve_pull_output(self):
        return sp.check_output('git pull'.split())

    def _collect_files_and_context(self, pull_output):
        context_files = {}
        base_path_regex_prefix = '%s\/' % self._repo_files_path if self._repo_files_path else ''
        basic_context_regex = r'%s([^\/]+).yaml' % base_path_regex_prefix
        basic_contexts = re.findall(basic_context_regex, pull_output)
        for context in basic_contexts:
            if context not in context_files:
                context_files[context] = []
            context_files[context].append(
                os.path.join(self._full_base_path, '%s.yaml' % context)
            )

        complex_path_regex = r'%s(.*?)\/(.*\.yaml)' % base_path_regex_prefix
        contexts = re.findall(complex_path_regex, pull_output)
        for context, file_path in contexts:
            if context not in context_files:
                dir_path = os.path.join(self._full_base_path, '%s' % context)
                file_list = list(filter(
                    lambda filename: filename.endswith('.yaml'),
                    os.listdir(dir_path)
                ))
                context_files[context] = [
                    os.path.join(dir_path, fname) for fname in file_list
                ]

        return context_files

    def get_path(self, context):
        return '%s/%s' % (self._base_path, context)

    def update_context_raw_data(self, file_list, zk, context):
        data = {}
        for filename in file_list:
            with open(filename, 'r') as f:
                d = yaml.load(f, yaml.FullLoader)
                data.update(d)
        raw_data = yaml.dump(data)
        raw_path = self.get_path(context)
        zk.ensure_path(raw_path)
        res = zk.set(raw_path, raw_data.encode())
        return res

    def update_context(self, context, file_list):
        zk = KazooClient(self._hosts)
        zk.start()
        try:
            self.update_context_raw_data(file_list, zk, context)
        finally:
            zk.stop()


if __name__ == '__main__':
    pass
