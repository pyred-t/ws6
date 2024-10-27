#!/usr/bin/env python3
import logging
import click

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

_CONFIG_PATH = 'config.cfg.sh'

configs = {}

def read_config():
    """
    append echo in the script to get the value of the variables
    """
    keys = []
    tmpfile = ''
    with open(_CONFIG_PATH, 'r') as file:
        with tempfile.NamedTemporaryFile('w', delete=False) as file2:
            tmpfile = file2.name
            file2.write("#!/bin/bash\n")    # shebang
            for line in file:
                file2.write(line + '\n')    # copy the content
                line = line.strip()
                if line and not line.startswith('#'):  # skip comments and empty lines
                    key, value = line.split('=', 1)
                    keys.append(key.strip())
            for key in keys:
                file2.write(f'echo ${key}\n')   # echo the value of the variables
            
            file2.flush()

    os.chmod(tmpfile, 0o755)
    try:
        result = subprocess.run([tmpfile], check=True, stdout=subprocess.PIPE, text=True)
        output = result.stdout.splitlines()
        for key, value in zip(keys, output):
            configs[key] = value
    finally:
        os.remove(tmpfile)

def _sourcebash_path(workspace:str) -> str:
    return f'{configs["_WS_ROOT"]}/{workspace}/devel/setup.bash'


@click.group()
def main():
    pass


def check_workspace(workspace:str, to_create:bool=False):
    if workspace == configs['_ROS']:
        return
    ws = pathlib.Path(configs['_WS_ROOT']).joinpath(workspace)
    if not ws.exists():
        if to_create:
            ws.mkdir()
            ws.joinpath('src').mkdir()
            logging.info(f'Workspace {workspace} created')
            subprocess.run(['catkin_make'], cwd=ws)
            return
        else:
            logging.error(f'\033[31m Workspace {workspace} does not exist \033[0m')
            sys.exit(1)
    
    logging.info(f'Workspace {workspace} exists')
    return


@main.command()
@click.argument('workspace')
def prepare_list(workspace:str):
    check_workspace(workspace)
    source_list = configs['_SOURCE_LIST']
    with open(source_list, 'w') as file:
        file.truncate(0)
        file.write('#!/bin/bash\n')
        file.write(f'source /opt/ros/{configs["_ROS"]}/setup.bash\n')
        if workspace == configs['_ROS']:
            return
        file.write(f'source {_sourcebash_path(configs["_WPB"])}\n')
        if workspace == configs['_WPB']:
            return
        file.write(f'source {_sourcebash_path(workspace)}\n')
    logging.info(f'Prepared source list for {workspace}')


@main.command()
@click.argument('workspace')
def start_p1(workspace:str):
    """
    first process of the start workflow: 
        create a new workspace if not exists (catkin_make),
        clone the repository to target branch, apply the patch, and create a new branch
    """
    check_workspace(workspace, to_create=True)
    ws = pathlib.Path(configs['_WS_ROOT']).joinpath(workspace)
    
    httpurl = input('Please input the http(s)url of the repository: ')
    branch = input('Please input the branch name(or press enter, default main): ') or 'main'
    tmpdir = tempfile.TemporaryDirectory()
    subprocess.run(['git', 'clone', '-b' , branch, httpurl, tmpdir.name], check=True)
    # ls -a src_dir | grep -v '^\.\.$' | grep -v '^\.$' | xargs -I {} cp -r src_dir/{} dst_dir/
    # subprocess.run(f'ls -a {tmpdir.name} | grep -v "^\\.$" | grep -v "^\\.\\.$" | xargs -I {{}} mv -f {tmpdir.name}/{{}} {ws}', shell=True, check=True)
    subprocess.run(f'mv -f {tmpdir.name}/* {ws}', shell=True, check=True)
    
    
    # subprocess.run(['git', 'apply', 'patch.diff'], cwd=ws)

    pass

def start_p2(workspace:str):
    """
    none
    """
    pass


def finish_p2(workspace:str):
    """
    first process of the finish workflow: 
        extract the patch, commit the changes, and push to the remote repository
        clean the repository
    """
    pass



if __name__ == '__main__':
    logging.basicConfig(format='\033[34m [WS6] %(levelname)s\033[0m: %(message)s', level=logging.INFO)
    read_config()
    print(configs)
    main()