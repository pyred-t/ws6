import os
import pathlib
import subprocess

if __name__ == '__main__':
    # git config --uset --global user.name user.emali
    # dir_name = os.path.basename('/home/username/Downloads/test')
    repo_path = '/home/m/s6'
    upstream = subprocess.run(['git', 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'], cwd=repo_path, capture_output=True, text=True)
    print(upstream.stdout)
    print(upstream.stdout.splitlines()[0])
