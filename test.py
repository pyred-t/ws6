import os
import pathlib
import subprocess

if __name__ == '__main__':
    diff_files = subprocess.run(['git', 'diff', '--name-only', 'origin/main'], check=True, capture_output=True, text=True)
    print(diff_files.stdout.splitlines())