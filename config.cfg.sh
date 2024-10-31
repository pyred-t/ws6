# Tool Paths and directories
_DEVELOPMENT="onboard"
_WS6_PY="./ws6.py"
_CACHE_DIR="."  # _CACHE_DIR="/var/cache/ws6"
_SOURCE_LIST="$_CACHE_DIR/source.list.sh"

# Workspace and ROS configuration
_WS_ROOT="/home/$(whoami)/ws"
_ROS="noetic"
_WPB="wpb_ws"

# Python configuration
_REQUIRED_PYTHON_PACKAGES="catkin-tools rosdep empy click"
_DEFAULT_PYTHON_VERSION="3.8"

# Git configuration
_PATCH_NAME="all_commits.patch"

# default master branch name is master
# if you want to use main branch, use the following format
# only use in wpb_ws now
# _{REPONAME}_MASTER="main"
# _{REPONAME}_REMOTE_MASTER="main"
