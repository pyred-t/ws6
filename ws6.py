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
                file2.write(line + '\n')
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

def _gen_branch_name(workspace:str) -> str:
    return f'{configs["_DEVELOPMENT"]}_{workspace}_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'

def _repo_master(repo_name:str) -> str:
    return configs[f'_{repo_name}_MASTER'] if f'_{repo_name}_MASTER' in configs else 'master'

def _repo_remote_master(repo_name:str) -> str:
    return configs[f'_{repo_name}_REMOTE_MASTER'] if f'_{repo_name}_REMOTE_MASTER' in configs else 'master'

# List[Pathlib.Path]
def _reset_wpb(repo_paths:list = None):
    subprocess.run(['git', 'config', '--unset', '--global', 'user.name'])
    subprocess.run(['git', 'config', '--unset', '--global', 'user.email'])
    repo_paths = [pathlib.Path(root) for root, dirs, _ in os.walk(wpb_ws.joinpath('src')) if '.git' in dirs] if repo_paths is None else repo_paths
    for repo_path in repo_paths:
        repo_name = repo_path.name
        try:
            result = subprocess.run(['git', 'branch', '--show-current'], cwd=repo_path, check=True, capture_output=True, text=True)
            branch_name = result.stdout.strip()
            subprocess.run(['git', 'checkout', f'{_repo_master(repo_name)}'], cwd=repo_path, check=True, stderr=subprocess.STDOUT)
            subprocess.run(['git', 'reset', '--hard', f'origin/{_repo_remote_master(repo_name)}'], cwd=repo_path, check=True, stderr=subprocess.STDOUT)
            subprocess.run(['git', 'branch', '-D', result.stdout], cwd=repo_path, check=True, stderr=subprocess.STDOUT) if branch_name != _repo_master(repo_name) else None
            logging.info(f'Reset the repository {repo_path}')
        except subprocess.CalledProcessError as e:
            logging.error(f'\033[31m Error in reset {repo_path}: {e.stderr}, skip this repo \033[0m')
    logging.info(f'\033[32m Reset the repositories in {configs["_WPB"]} \033[0m')


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
    wpb_ws = pathlib.Path(configs['_WS_ROOT']).joinpath(configs['_WPB'])

    # try reset wpb_ws
    _reset_wpb()

    
    httpurl = input('Please input the http(s)url of the repository: ')
    branch = input('Please input the branch name(or press enter, default main): ') or 'main'
    tmpdir = tempfile.TemporaryDirectory()
    subprocess.run(['git', 'clone', '-b' , branch, httpurl, tmpdir.name], check=True, stderr=subprocess.STDOUT)
    subprocess.run(['rsync', '-a', f'{tmpdir.name}/', f'{ws}/'], check=True, stderr=subprocess.STDOUT)

    # apply the patch
    patch_path = ws.joinpath('external', 'patches')
    for rel_to_src in patch_path.iterdir():
        repo_path = wpb_ws.joinpath('src', rel_to_src)
        if repo_path not in wpb_repo_paths:
            logging.warning(f'\033[33m repo {repo_path} does not exist \033[0m')
            continue
        patch_file = rel_to_src.joinpath(configs['_PATCH_NAME'])
        if not patch_file.exists():
            logging.warning(f'\033[33m patch file {patch_file} does not exist \033[0m')
            continue
        subprocess.run(['git', 'am', patch_file], cwd=repo_path, check=True, stderr=subprocess.STDOUT)
        logging.info(f'Patch applied to {repo_path}')
    
    # create a new branch
    try:
        for repo_path in wpb_repo_paths:
            branch_name = _gen_branch_name(workspace)
            subprocess.run(['git', 'checkout', '-b', branch_name], cwd=repo_path, check=True, stderr=subprocess.STDOUT)
            logging.info(f'Created a new branch {branch_name} in {repo_path}')
        
        branch_name = _gen_branch_name(workspace)
        subprocess.run(['git', 'checkout', '-b', branch_name], cwd=ws, check=True, stderr=subprocess.STDOUT)
        logging.info(f'Created a new branch {branch_name} in {ws}')
    except:
        logging.error(f'\033[31m Error in creating a new branch, skip those \033[0m')
    
    logging.info(f'\033[32m Finish repo workflow.\033[0m \n '
                '\t\033[33m You may check user.name and user.email in each repo or global. now\033[0m')

@main.command()
@click.argument('workspace')
@click.argument('done_all_yes', type=bool, default=False)
def finish_p2(workspace:str, done_all_yes:bool=False):
    """
    second process of the finish workflow: 
        extract the patch, commit the changes, and push to the remote repository
        clean the repository
    """
    # traversal wpb_ws to find folder containing .git folder and check if there are uncommitted changes
    ws = pathlib.Path(configs['_WS_ROOT']).joinpath(workspace)
    wpb_ws = pathlib.Path(configs['_WS_ROOT']).joinpath(configs['_WPB'])

    def check_uncommitted_changes(repo_path: pathlib.Path):
        result = subprocess.run(['git', 'status', '--porcelain'], cwd=repo_path, check=True, capture_output=True, text=True)
        if result.stdout:
            print('\n', result.stdout)
            logging.error(f'\033[31m {repo_path} has uncommitted changes. Please commit or stash your changes before proceeding. \033[0m\n'
                        f'\t\033[33m Or try: git -C {repo_path} commit -am "autocommit message {datetime.datetime.now()}" \033[0m')
            sys.exit(1)

    # wpb repos
    repo_paths = [pathlib.Path(root) for root, dirs, _ in os.walk(wpb_ws.joinpath('src')) if '.git' in dirs]
    for repo_path in repo_paths:
        check_uncommitted_changes(repo_path)
    
    # save the patch files and diff files
    for repo_path in repo_paths:
        diff_files = subprocess.run(['git', 'diff', '--name-only', 'origin/master'], cwd=repo_path, capture_output=True, text=True)
        if diff_files.stderr:
            logging.error(f'Error in {repo_path}: {diff_files.stderr}')
            sys.exit(1)
        
        rel_to_src = repo_path.relative_to(wpb_ws.joinpath('src'))
        # clean old
        subprocess.run(['rm', '-rf', ws.joinpath('external', 'patches', rel_to_src)], check=True)
        subprocess.run(['rm', '-rf', ws.joinpath('external', 'diffs_read_only', rel_to_src)], check=True)
        if not diff_files.stdout.strip():
            logging.info(f'No changes in {repo_path}')
            continue
        # copy
        patch_path = ws.joinpath('external', 'patches', rel_to_src)
        diff_path = ws.joinpath('external', 'diffs_read_only', rel_to_src)
        patch_path.mkdir(parents=True, exist_ok=True)
        diff_path.mkdir(parents=True, exist_ok=True)
        for file in diff_files.stdout.splitlines():
            diff_path.joinpath(file).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(repo_path.joinpath(file), diff_path.joinpath(file).parent)
        subprocess.run(
            ['git', 'format-patch', 'origin/master..HEAD', '--stdout'], 
            cwd=repo_path, check=True, stdout=patch_path.joinpath(configs['_PATCH_NAME']).open('w')
        )

    logging.info(f'Patch files are saved in {ws.joinpath("external", "patches")}')
    
    if not done_all_yes:
        logging.info('\033[33m Finish the repo workflow without pushing the changes \033[0m')
        sys.exit(2)
    
    # Try auto commit the patch files, error msg redirect to null
    subprocess.run(['git', 'add', 'external/patches/'], cwd=ws, stderr=subprocess.DEVNULL)
    subprocess.run(['git', 'commit', '-m', f'Add patches for {workspace}'], cwd=ws, stderr=subprocess.DEVNULL)
    
    # push the changes
    check_uncommited_changes(ws)
    result = subprocess.run(['git', 'branch', '--show-current'], cwd=ws, check=True, capture_output=True, text=True)
    branch_name = result.stdout.strip()
    # git upstream name
    upstream = subprocess.run(['git', 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'], cwd=ws, capture_output=True)
    if upstream.returncode:
        logging.warning(f'\033[33m Error in getting upstream branch: {upstream.stderr} \033[0m')
        upstream = ''
    else:
        upstream = upstream.stdout.strip()
    
    if upstream:
        anystr = input(f'will push {branch_name} to {upstream}, input "yes" to continue, or input "no" to abort: ')
        if anystr != 'yes' or anystr != 'y':
            logging.info(f'\033[33m Finish the repo workflow without pushing the changes \033[0m')
            sys.exit(2)
        else:
            subprocess.run(['git', 'push'], cwd=ws, check=True, stderr=subprocess.STDOUT)
    else:
        anystr = input(f'no upstream branch found, will push {branch_name} to origin, input "yes" to continue, or input "no" to abort: ')
        if anystr != 'yes' or anystr != 'y':
            logging.info(f'\033[33m Finish the repo workflow without pushing the changes \033[0m')
            sys.exit(2)
        else:
            subprocess.run(['git', 'push', 'origin', branch_name], cwd=ws, check=True, stderr=subprocess.STDOUT)
    
    logging.info(f'\033[34m Changes are pushed to the remote repository \033[0m')
    logging.info(f'would clean the repository metainfo and reset the wpb_ws now')

    # rm .git folder
    subprocess.run(['rm', '-rf', ws.joinpath('.git')], check=True)
    logging.info(f'\033[32m Cleaned the repository metainfo \033[0m')
    # reset the wpb_ws
    _reset_wpb(repo_paths)

    logging.info(f'\033[32m Finish repo workflow. You may delete {"{workspace}"}/src manually now. \033[0m')


if __name__ == '__main__':
    logging.basicConfig(format='\033[34m [WS6] %(levelname)s\033[0m: %(message)s', level=logging.INFO)
    read_config()
    main()
