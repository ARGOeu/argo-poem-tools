import os
import shutil
import subprocess


class YUMRepos:
    def __init__(self, data, repos_path='/etc/yum.repos.d', override=True):
        self.data = data
        self.path = repos_path
        self.override = override
        self.missing_packages = None

    def create_file(self, include_internal=False):
        files = []
        for key, value in self.data.items():
            title = key
            filename = os.path.join(self.path, title + '.repo')
            content = value['content']

            files.append(filename)

            if not self.override:
                os.makedirs('/tmp' + self.path, exist_ok=True)
                if os.path.isfile(filename):
                    shutil.copyfile(filename, '/tmp' + filename)

            with open(filename, 'w') as f:
                f.write(content)

        return sorted(files)

    def clean(self):
        if not self.override:
            tmp_dir = '/tmp' + self.path
            if os.path.isdir(tmp_dir):
                src_files = os.listdir(tmp_dir)
                for file in src_files:
                    full_filename = os.path.join(tmp_dir, file)
                    if os.path.isfile(full_filename):
                        shutil.copy(full_filename, self.path)

                shutil.rmtree(tmp_dir)

        subprocess.call(['yum', 'clean', 'all'])
