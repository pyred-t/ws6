#!/bin/bash

SCRIPT_PATH=$(realpath $0)
SCRIPT_DIR=$(dirname $SCRIPT_PATH)
ENTRY_DIR=$(dirname $SCRIPT_DIR)
ENTRY_SH=$ENTRY_DIR/entry.sh

# set conda auto activate base off and changeps1 off
conda info &>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: conda not found"
    exit 1
fi
conda config --set auto_activate_base false
conda config --set changeps1 False

# prepare etc directory
CFG_PATH=$ENTRY_DIR/config.cfg.sh
if [ ! -f $CFG_PATH ]; then
    echo "Error: config.cfg.sh not found"
    exit 1
fi
# rewrite config.cfg.sh, set WS6_HOME to ENTRY_DIR
sed -i "s#WS6_HOME=.*#WS6_HOME=\"$ENTRY_DIR\"#" $CFG_PATH
source $CFG_PATH

# convert relative path to absolute path
if [[ $_CACHE_DIR != /* ]]; then
    _CACHE_DIR=$(realpath $ENTRY_DIR/$_CACHE_DIR)
fi
if [[ $_SOURCE_LIST != /* ]]; then
    _SOURCE_LIST=$(realpath $ENTRY_DIR/$_SOURCE_LIST)
fi

mkdir -p $_CACHE_DIR
if [ ! -f $_SOURCE_LIST ]; then
    touch $_SOURCE_LIST
fi

####### bashrc ########
if [ -z "$(grep "ws6: update bashrc" ~/.bashrc)" ]; then
    echo "# >>> ws6: update bashrc >>>" >> ~/.bashrc
fi

 if [ -z "$(grep WS6_HOME ~/.bashrc)" ]; then
     echo "export WS6_HOME=\"$WS6_HOME\"" >> ~/.bashrc
 fi

# alias ws6 = `source entry.sh`
if [ -z "$(grep "alias ws6=" ~/.bashrc)" ]; then
    echo "alias ws6='source $ENTRY_SH'" >> ~/.bashrc
fi

# add source list to bashrc
if [ -z "$(grep "source $_SOURCE_LIST" ~/.bashrc)" ]; then
    echo "source $_SOURCE_LIST" >> ~/.bashrc
fi


# ps1 content
KEYWORDS_CONTENT="
get_ros_keywords() { 
    echo \"\$ROS_PACKAGE_PATH\" | tr ':' '\n' | awk -F'/' '{print \$(NF-1)}' 2>/dev/null | paste -sd ';' -
}"

CONDA_CONTENT="
get_conda_env() {
    basename \"\$CONDA_PREFIX\" 2>/dev/null
}"

PS1_CONTENT="export PS1='(\$(get_conda_env)) \[\e[32m\]\u@\h\[\e[33m\][\$(get_ros_keywords)]\[\e[0m\]:\w\$ '"

if [ -z "$(grep "get_conda_env" ~/.bashrc)" ]; then
    echo "$CONDA_CONTENT" >> ~/.bashrc
fi
if [ -z "$(grep "get_ros_keywords" ~/.bashrc)" ]; then
    echo "$KEYWORDS_CONTENT" >> ~/.bashrc
    echo "$PS1_CONTENT" >> ~/.bashrc
fi
if [ -z "$(grep "ws6: update bashrc finished" ~/.bashrc)" ]; then
    echo "# <<< ws6: update bashrc finished <<<" >> ~/.bashrc
fi
