import os
import pathlib
import subprocess

if __name__ == '__main__':
    # git config --uset --global user.name user.emali
    # dir_name = os.path.basename('/home/username/Downloads/test')
    repo_path = pathlib.Path('/home/m/s6')
    sub = repo_path.joinpath('.etc')
    sub.mkdir(parents=True, exist_ok=True)
    print(sub.exists(), sub.is_dir())
    print(sub)
    
    
