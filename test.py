import os
import pathlib
import subprocess

if __name__ == '__main__':
    # git config --uset --global user.name user.emali
    # dir_name = os.path.basename('/home/username/Downloads/test')
    dir_name2 = pathlib.Path('/home/username/Downloads/test').name
    print(dir_name2)
