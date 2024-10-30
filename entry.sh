#!/bin/bash

source config.cfg.sh

# Rebase the workspace to establish the correct overlay. 
# $1 is the workspace name, and $2 (if provided) indicates a forced rebuild.
# Mind: never use conda env to pollute base ros workspace
function rebase() {
    unset ROS_PACKAGE_PATH
    $_WS6_PY prepare-list $1 && source $_SOURCE_LIST
    if [ $? -ne 0 ]; then echo -e "\e[31m Error check workspace $1 \e[0m"; return 1; fi
    if [[ "$1" == "$_ROS" ]]; then
        echo -e "\e[32m Successfully rebase workspace $1 \e[0m"
        return 0
    fi
    # the following section may rebuild the target workspace to establish the correct overlay
    pkg_count=$(echo "$ROS_PACKAGE_PATH" | awk -F':' '{print NF}')
    echo -e "\e[34m ROS_PACKAGE_PATH contains $pkg_count packages \e[0m"
    if [[ "$1" == "$_WPB" || -n "$2" ]]; then
        if [ $pkg_count -ne 2 ]; then
            rebase $_ROS                                                        # Check carefully: recursive call
            pushd $_WS_ROOT/$_WPB && rm -rf devel build && catkin_make && popd
            [ $? -ne 0 ] && echo -e "\e[31m Error rebuild $_WPB \e[0m" && return 1
            $_WS6_PY prepare-list $_WPB && source $_SOURCE_LIST
        fi
    else
        if [[ $pkg_count -ne 3 || -n "$2" ]]; then
            rebase $_WPB $2                                                     # Check carefully: recursive call
            pushd $_WS_ROOT/$1 && rm -rf devel build && catkin_make && popd
            [ $? -ne 0 ] && echo -e "\e[31m Error rebuild $1 \e[0m" && return 1
            $_WS6_PY prepare-list $1 && source $_SOURCE_LIST
        fi
    fi
    echo -e "\e[32m Successfully rebase workspace $1 \e[0m"
}


function start() {
    # TODO: unset global git config
    # p1: check or create workspace, clone git repo, apply patch
    $_WS6_PY start_p1 $1

    # p2: activate/create conda env (conda name forced to be same as workspace name) and update environemt by env.yml
    conda_env_list=`conda env list | awk '{print $1}'`
    if [[ $conda_env_list =~ $1 ]]; then
        echo "\e[32m Use Conda env $1 \e[0m"
    else
        read -p "Enter the Python version for the conda environment (default is $_DEFAULT_PYTHON_VERSION): " python_version
        python_version=${python_version:-$_DEFAULT_PYTHON_VERSION}
        echo -e "\e[33m Creating new Conda environment $1 \e[0m"
        conda create -n $1 python=$python_version $_REQUIRED_PYTHON_PACKAGES
    fi
    [ $? -ne 0 ] && echo -e "\e[31m Error create conda env $1 \e[0m" && return 1
    conda activate $1
    # TODO: conda env update by env.yml
    
    # p3: force rebuild rebase
    rebase $1 force
}


# $1 is the workspace name, 
# and $2 (if provided, “1”, “true”, “t”, “yes”, “y”) indicates do all finish steps including delete git repo metadata
function finish() {
    $_WS6_PY validate-workspace $1
    if [ $? -ne 0 ]; then
        echo "Error validate workspace $1"
        return 1
    fi

    # p1: prepare conda env.yml
    echo -e "Exporting conda env $1 to $_WS_ROOT/$1/env.yml"
    conda export -n $1 --no-builds -f $_WS_ROOT/$1/env.yml
    [ $? -ne 0 ] && echo -e "\e[31m Error export conda env $1 \e[0m" && return 1

    # p2: git things
    $_WS6_PY finish-p2 $1 $2
    if [ $? -eq 2 ]; then
        echo -e "\e[32m Successfully finished workspace without done-all $1 \e[0m"
    elif [ $? -ne 0 ]; then
        echo -e "\e[31m Terminate work on finishing workspace $1 \e[0m"
        return 1
    fi
    
    # p3: deactivate conda env or change to base
    conda deactivate

    # p4: rebase workspace ros
    rebase $_ROS
}


function delete() {
    ret = `$_WS6_PY check-workspace $1`
    if [ -n $ret ]; then
        echo "Error check workspace $1, err: $ret"
        return 1
    fi

    # p1: delete conda env

    # p2: delete workspace

    # p4: rebase workspace ros
    rebase $_ROS
}


function main() {
    case $1 in
        "rebase")
            rebase $2 $3
            ;;
        "start")
            start $2
            ;;
        "finish")
            finish $2 $3
            ;;
        "delete")
            delete $2
            ;;
        *)
            echo "Usage: $0 {rebase|start|finish|delete} {workspace_name}"
            exit 1
    esac
}

main $@