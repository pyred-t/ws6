_DEVELOPMENT="simulation"
# Do not change. Tool Paths and directories
WS6_HOME="/home/m/s6"
_SCRIPTS_DIR="$WS6_HOME/scripts"
_CACHE_DIR="$WS6_HOME/.etc"
_WS6_PY="$_SCRIPTS_DIR/ws6.py"
_SOURCE_LIST="$_CACHE_DIR/source.list.sh"

# Do not change. conda env, auto detect
if [ -n "$CONDA_PREFIX" ]; then
    _CURRENT_CONDA_ENV=$(basename $CONDA_PREFIX)
fi

# Workspace and ROS configuration
_WS_ROOT="/home/$(whoami)/ws"
_ROS="noetic"
_WPB="wpb_ws"

# Python configuration
_REQUIRED_PYTHON_PACKAGES_BY_CONDA="rosdep empy click"
_REQUIRED_PYTHON_PACKAGES_BY_PIP="catkin-tools"
_DEFAULT_PYTHON_VERSION="3.8"

# Git configuration
_PATCH_NAME="all_commits.patch"

# default master branch name is master
# if you want to use main branch, use the following format
# only use in wpb_ws now
# _{REPONAME}_MASTER="main"
# _{REPONAME}_REMOTE_MASTER="main"
