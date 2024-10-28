import os
import pathlib

if __name__ == '__main__':
    wpb_ws = pathlib.Path('~/ws/wpb_ws').expanduser()
    for root, dirs, files in os.walk(os.path.expanduser('~/ws/wpb_ws/src')):
        if '.git' in dirs:
            repo_path = pathlib.Path(root)
            rel_to_src = repo_path.relative_to(wpb_ws.joinpath('src'))
            print(repo_path, rel_to_src)
        # for name in files:
        #     print(os.path.join(root, name))
        # for name in dirs:
        #     print(os.path.join(root, name))