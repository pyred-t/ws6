#!/usr/bin/env python3
import logging
import click

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import datetime

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


def _check_workspace(workspace:str, to_create:bool=False):
    if workspace == configs['_ROS']:
        return
    ws = pathlib.Path(configs['_WS_ROOT']).joinpath(workspace)
    if not ws.exists():
        if to_create:
            ws.joinpath('src').mkdir(parents=True, exist_ok=True)
            subprocess.run(['catkin_make'], cwd=ws, check=True)
            ws.joinpath('external').mkdir(parents=True, exist_ok=True)
            logging.info(f'Workspace {workspace} created')
            return
        else:
            logging.error(f'\033[31m Workspace {workspace} does not exist \033[0m')
            sys.exit(1)
    
    logging.info(f'Workspace {workspace} exists')


@main.command()
@click.argument('workspace')
def validate_workspace(workspace:str):
    if workspace == configs['_ROS'] or workspace == configs['_WPB']:
        logging.error(f'\033[31m {workspace} is a reserved workspace name \033[0m')
        sys.exit(1)
    _check_workspace(workspace)


@main.command()
@click.argument('workspace')
def prepare_list(workspace:str):
    _check_workspace(workspace)
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
    _check_workspace(workspace, to_create=True)
    ws = pathlib.Path(configs['_WS_ROOT']).joinpath(workspace)
    
    httpurl = input('Please input the http(s)url of the repository: ')
    branch = input('Please input the branch name(or press enter, default main): ') or 'main'
    tmpdir = tempfile.TemporaryDirectory()
    subprocess.run(['git', 'clone', '-b' , branch, httpurl, tmpdir.name], check=True, stderr=subprocess.STDOUT)
    subprocess.run(['rsync', '-a', f'{tmpdir.name}/', f'{ws}/'], check=True, stderr=subprocess.STDOUT)

    # apply the patch

    # create a new branch
    
    
    # subprocess.run(['git', 'apply', 'patch.diff'], cwd=ws)

    pass


def finish_p2(workspace:str, skip_push:bool=False):
    """
    first process of the finish workflow: 
        extract the patch, commit the changes, and push to the remote repository
        clean the repository
    """
    ws = pathlib.Path(configs['_WS_ROOT']).joinpath(workspace)
    # check if the repo has uncommitted changes
    result = subprocess.run(['git', 'status', '--porcelain'], cwd=ws, check=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print(res.stdout)
        logging.error(f'\033[31m {ws} has uncommitted changes. Please commit or stash your changes before proceeding. \033[0m'
                    f'\033[31m Or try: git -C {ws} commit -am "autocommit message{datetime.datetime.now()}" \033[0m')
        sys.exit(1)

    # traversal wpb_ws to find folder containing .git folder and check if there are uncommitted changes
    wpb_ws = pathlib.Path(configs['_WS_ROOT']).joinpath(configs['_WPB'])
    repo_pahts = []
    for root, dirs, files in os.walk(wpb_ws.joinpath('src')):
        if '.git' in dirs:
            repo_path = pathlib.Path(root)
            # check if the repo has things to commit
            result = subprocess.run(['git', 'status', '--porcelain'], cwd=repo_path, check=True, capture_output=True, text=True)
            if not result.stdout.strip():
                print(result.stdout)
                logging.error(f'\033[31m {repo_path} has uncommitted changes. Please commit or stash your changes before proceeding. \033[0m'
                            f'\033[31m Or try: git -C {repo_path} commit -am "autocommit message{datetime.datetime.now()}" \033[0m')
                sys.exit(1)
            repo_pahts.append(repo_path)
    # save the patch files
    for repo_path in repo_pahts:
        rel_to_src = repo_path.relative_to(wpb_ws.joinpath('src'))
        patch_path = ws.joinpath('external', 'patches', rel_to_src)
        patch_path.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ['git', 'format-patch', 'origin/master..HEAD', '--stdout'], 
            cwd=repo_path, check=True, stdout=patch_path.joinpath(configs['_PATCH_NAME']).open('w')
        )
    logging.info(f'Patch files are saved in {ws.joinpath("external", "patches")}')
    
    if skip_push:
        logging.info('\033[33m Finish the repo workflow without pushing the changes \033[0m')
        return

    # push the changes
    subprocess.run(['git', 'push'], cwd=ws, check=True)
    logging.info(f'\033[34m Changes are pushed to the remote repository \033[0m')
    # rm .git folder
    subprocess.run(['rm', '-rf', ws.joinpath('.git')], check=True)
    logging.info(f'\033[32m Cleaned the repository metainfo \033[0m')
    # reset the wpb_ws
    for repo_path in repo_pahts:
        # get git branch name
        result = subprocess.run(['git', 'branch', '--show-current'], cwd=repo_path, check=True, capture_output=True, text=True)
        subprocess.run(['git', 'checkout', 'master'], cwd=repo_path, check=True)
        subprocess.run(['git', 'reset', '--hard', 'origin/master'], cwd=repo_path, check=True)
        subprocess.run(['git', 'branch', '-D', result.stdout.strip()], cwd=repo_path, check=True)
        logging.info(f'Reset the repository {repo_path}')
    logging.info(f'\033[32m Reset the repositories in {configs["_WPB"]} \033[0m')

    logging.info(f'\033[32m Finish repo workflow. You may delete {"{workspace}"}/src manually now. \033[0m')



if __name__ == '__main__':
    logging.basicConfig(format='\033[34m [WS6] %(levelname)s\033[0m: %(message)s', level=logging.INFO)
    read_config()
    print(configs)
    main()