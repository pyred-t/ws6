import os
import pathlib
import subprocess

if __name__ == '__main__':
    # git config --uset --global user.name user.emali
    subprocess.run(['git', 'config', '--unset', '--global', 'user.name'])
    subprocess.run(['git', 'config', '--unset', '--global', 'user.email'])