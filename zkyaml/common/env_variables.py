import os
current_dir = os.getcwd()
default_repo_path = os.environ.get('ZKYAML_REPO_PATH', current_dir)
default_repo_files_path = os.environ.get('ZKYAML_CONFIG_FILES_PATH', 'vc')
default_single_files_path = os.environ.get('ZKYAML_SINGLE_FILES_PATH', 'vc_yaml')
default_base_path = os.environ.get('ZKYAML_ZK_BASE_PATH', 'vc_yaml')
