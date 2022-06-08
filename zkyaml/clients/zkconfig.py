import yaml
import logging
import threading
import logging.config
from kazoo.client import KazooClient

logger = logging.getLogger()


class AutoUpdatedConfig:
    def __init__(self,data,central_config):
        self._data = data
        self._central_config = central_config
        self._need_to_update = False

    def notify(self, *args, **kwargs):
        self._need_to_update = True

    def check_update(self):
        try:
            if self._need_to_update:
                self.update(self._central_config._get_config_dict())
        except:
            pass

    def update(self, config):
        if isinstance(config, dict):
            return self._data.update(config)
        elif isinstance(config, AutoUpdatedConfig):
            return self._data.update(config._data)

    def get(self, key, default=None):
        self.check_update()
        return self._data.get(key,default)

    def __getitem__(self, item):
        self.check_update()
        return self._data[item]

    def __contains__(self, item):
        self.check_update()
        return item in self._data

    def get_data(self):
        self.check_update()
        return self._data

    def __repr__(self):
        return self._data.__repr()

    def __str__(self):
        return self._data.__str__()


class ZookeeperDataWatcher:
    def __init__(self, path, centeral_config):
        self._centeral_config = centeral_config
        self._path = path
    def __call__(self, *args, **kwargs):
        result = True
        try:
            event = args[2]
            if event:
                if event.type == 'DELETED':
                    result =  False
                elif event.type == 'CHANGED':
                    result =  True
                self._centeral_config._handle_watch(*args, **kwargs)
        except:
            logging.exception('ZookeeperDataWatcher failed')
        return result


class ZKUtils:
    @staticmethod
    def resolve_diff(old_data,new_data):
        diff_dict = {}
        for k,v in new_data.items():
            if k not in old_data or v != old_data[k]:
                diff_dict[k] = v
        for k,v in old_data.items():
            if k not in new_data:
                diff_dict[k] = v

        return diff_dict


class ZKConfig:
    def __init__(self, hosts, context_list, watch=True):
        self._hosts = hosts
        self._context_list = context_list
        self._config = None
        self._observers = []
        self._fetch_config_lock = threading.RLock()

        # Start zookeeper.
        self._zk = KazooClient(self._hosts)
        self._zk.start()

        # Fetch config for the first time.
        with self._fetch_config_lock:
            self._get_config()

        self._data_watchers = {}
        self._watch_callback_runinng = False
        self._update_on_watch = False
        self._fetch_config = False

        if watch:
            self._watch()
        else:
            self._zk.stop()

    def _watch(self):
        self._update_on_watch = False
        for c in self._context_list:
            self._zk.ensure_path(c)
        self._update_on_watch = True

    def _handle_watch(self, *args, **kwargs):
        if self._update_on_watch:
            self._fetch_config = True
            self.fetch_config()

    def fetch_config(self):
        try:
            with self._fetch_config_lock:
                if self._fetch_config:
                    old_data = self._config
                    self._get_config()
                    print(('Zookeeper: Config Updated: %s' % str(ZKUtils.resolve_diff(old_data,self._config))))
                    self._fetch_config = False

        except Exception as e:
            print(('Zookeeper: Error Fetching Config Thread: %s'% e))

    def get_config(self):
        auto_updated_config = AutoUpdatedConfig(self._config,self)
        self._observers.append(auto_updated_config)
        return auto_updated_config

    def _get_config_dict(self):
        return self._config

    def _get_config(self):
        """
        load config from zookeeper
        :return: dict
        """
        try:
            zk = self._zk
            global_config = {}
            for cr in self._context_list:
                context_config_yaml, s = zk.get(cr)
                context_config = yaml.load(context_config_yaml, Loader=yaml.FullLoader)
                if context_config:
                    global_config.update(context_config)
            # context config overrides the global config
            self._config = global_config
            for obserever in self._observers:
                obserever.notify(self._config)
            print('Zookeeper Config Fetched')
        except:
            logger.exception('Zookeeper failed!')
            self._config = None