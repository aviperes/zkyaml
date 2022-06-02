import os
current_dir = os.getcwd()
default_repo_path = os.environ.get('ZKYAML_REPO_PATH', current_dir)
default_repo_files_path = os.environ.get('ZKYAML_FILES_PATH', 'vc')
default_base_path = os.environ.get('ZKYAML_ZK_BASE_PATH', 'vc_yaml')
