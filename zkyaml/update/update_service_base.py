import os
import subprocess as sp
from abc import ABCMeta, abstractmethod


class UpdateServiceBase(object, metaclass=ABCMeta):
    def update(self):
        if self._changed():
            return self._update()
        return True

    @abstractmethod
    def _changed(self):
        raise NotImplementedError

    @abstractmethod
    def _update(self):
        raise NotImplementedError


class UpdateGitServiceBase(UpdateServiceBase, metaclass=ABCMeta):
    def __init__(self):
        super(UpdateGitServiceBase, self).__init__()
        self._current_branch_name = None

    @abstractmethod
    def _get_path_to_repository(self):
        raise NotImplementedError

    @abstractmethod
    def _get_branch_name(self):
        raise NotImplementedError

    # Implements abstractmethod
    def _changed(self):
        path_to_repository = self._get_path_to_repository()
        os.chdir(path_to_repository)

        branch_name = self._get_branch_name()
        if self._current_branch_name is not None and self._current_branch_name != branch_name:
            self._current_branch_name = branch_name
            checkout_command = 'git checkout %s' % self._get_branch_name()
            sp.call(checkout_command.split())
            return True

        sp.call('git fetch'.split())

        branch_name = self._get_branch_name()
        git_command = 'git log HEAD..origin/%s --oneline' % branch_name
        changed = sp.check_output(git_command.split())

        return changed

    def _set_current_branch(self, branch_name):
        self._current_branch_name = branch_name