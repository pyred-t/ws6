#!/bin/bash

source "$WS6_HOME/config.cfg.sh"

# Rebase the workspace to establish the correct overlay. 
# $1 is the workspace name, and $2 (if provided) indicates a forced rebuild.
# Mind: never use conda env to pollute base ros workspace
function rebase() {
    if [ -z "$1" ]; then
        help
        return 1
    fi
    if [ -n "$2" ] && [ "$2" != "force" ]; then
        help
        return 1
    fi

    unset ROS_PACKAGE_PATH
    $_WS6_PY prepare-list $1 && source $_SOURCE_LIST
    if [ $? -ne 0 ]; then echo -e "\e[31m Error check workspace $1 \e[0m"; return 1; fi
    if [[ "$1" == "$_ROS" ]]; then
        while [[ "$CONDA_PREFIX" != "" ]]; do
            conda deactivate
        done
        echo -e "\e[32m Successfully rebase workspace $1 \e[0m"
        return 0
    fi
    # the following section may rebuild the target workspace to establish the correct overlay
    pkg_count=$(echo "$ROS_PACKAGE_PATH" | awk -F':' '{print NF}')
    echo -e "\e[34m ROS_PACKAGE_PATH contains $pkg_count packages \e[0m"
    if [[ "$1" == "$_WPB" ]]; then
        if [[ $pkg_count -ne 2 || -n "$2" ]]; then
            rebase $_ROS                                                        # Check carefully: recursive call
            pushd $_WS_ROOT/$_WPB && rm -rf devel build && catkin_make 
            [ $? -ne 0 ] && echo -e "\e[31m Error rebuild $_WPB \e[0m" && popd && return 1
            popd
            $_WS6_PY prepare-list $_WPB && source $_SOURCE_LIST
        fi
    else
        if [[ $pkg_count -ne 3 || -n "$2" ]]; then
            rebase $_WPB $2                                                     # Check carefully: recursive call
            [ $? -ne 0 ] && echo -e "\e[31m Error rebase $_WPB \e[0m" && return 1
            pushd $_WS_ROOT/$1 && rm -rf devel build && catkin_make
            [ $? -ne 0 ] && echo -e "\e[31m Error rebuild $1 \e[0m" && popd && return 1
            popd
            $_WS6_PY prepare-list $1 && source $_SOURCE_LIST
        fi
    fi
    echo -e "\e[32m Successfully rebase workspace $1 \e[0m"
}

# $1 is the workspace name
function start() {
    to_create=0
    $_WS6_PY validate-workspace $1
    ret=$?
    if [ $ret -ne 0 ] && [ $ret -ne 11 ]; then
        to_create=1
    fi
    
    # p1: check or create workspace, clone git repo, apply patch
    $_WS6_PY start-p1 $1
    if [ $? -ne 0 ]; then
        echo -e "\e[31m Error start workspace $1 \e[0m"
        # if to_create, delete the workspace
        if [ $to_create -eq 1 ]; then
            rm -rf $_WS_ROOT/$1
        fi
        return 1
    fi

    # p2: activate/create conda env (conda name forced to be same as workspace name) and update environemt by env.yml
    conda_env_list=`conda env list | awk '{print $1}'`
    if [[ $conda_env_list =~ $1 ]]; then
        echo -e "\e[32m Use Conda env $1 \e[0m"
    else
        read -p "Enter the Python version for the conda environment (default is $_DEFAULT_PYTHON_VERSION): " python_version
        python_version=${python_version:-$_DEFAULT_PYTHON_VERSION}
        echo -e "\e[33m Creating new Conda environment $1 \e[0m"
        conda create -n $1 python=$python_version $_REQUIRED_PYTHON_PACKAGES_BY_CONDA -y && conda activate $1
        if [ -n "$_REQUIRED_PYTHON_PACKAGES_BY_PIP" ]; then
            pip install $_REQUIRED_PYTHON_PACKAGES_BY_PIP
        fi
    fi
    [ $? -ne 0 ] && echo -e "\e[31m Error create conda env $1 \e[0m" && return 1
    # conda env update by env.yml
    conda activate $1
    if [ -f $_WS_ROOT/$1/env.yml ]; then
        conda env update -n $1 -f $_WS_ROOT/$1/env.yml
        if [ $? -ne 0 ]; then
            echo -e "\e[31m Error update conda env $1 \e[0m"
            echo -e "Please check the env.yml file and update the conda env manually by 'conda env update -n $1 -f $_WS_ROOT/$1/env.yml',"
            echo -e "and run 'rebase $1 force' to establish the correct overlay"
            echo -e "\e[33m All works done except 'rebase $1 force' \e[0m"
            return 1
        fi
    fi
    
    # p3: force rebuild rebase
    rebase $1 force
    [ $? -ne 0 ] && echo -e "\e[31m Error rebase $1 \e[0m" && return 1
    echo -e "\e[32m Successfully start workspace $1 \e[0m"
}


# $1 is the workspace name, 
# and $2 (done-all) indicates do all finish steps including delete git repo metadata
function finish() {
    if [ -z "$1" ]; then
        help
        return 1
    fi
    if [ -n "$2" ]; then
        if [ "$2" != "done-all" ]; then
            help
            return 1
        else
            done_all=y
        fi
    fi


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
    ret=$?
    if [ $ret -eq 2 ]; then
        echo -e "\e[32m Successfully finished workspace without done-all $1 \e[0m"
        return 0
    elif [ $ret -ne 0 ]; then
        echo -e "\e[31m Terminate work on finishing workspace $1 \e[0m"
        return 1
    fi
    
    # p3: deactivate conda env
    while [[ "$CONDA_PREFIX" != "" ]]; do
        conda deactivate
    done

    # p4: rebase workspace ros
    rebase $_ROS
    echo -e "\e[32m Successfully finished workspace $1 \e[0m"
}


# function delete() {
#     $_WS6_PY validate-workspace $1
#     if [ $? -ne 0 ]; then
#         echo "Error validate workspace $1"
#         return 1
#     fi

#     # p1: delete conda env
#     conda env remove -n $1
#     [ $? -ne 0 ] && echo -e "\e[31m Error delete conda env $1 \e[0m" && return 1

#     # p2: delete workspace
#     rm -rf $_WS_ROOT/$1
#     [ $? -ne 0 ] && echo -e "\e[31m Error delete workspace $1 \e[0m" && return 1

#     # p4: rebase workspace ros
#     rebase $_ROS
# }


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
        *)
            help
            return 1
    esac
}

function help() {
    echo "Usage: ws6 start {workspace_name}"
    echo "Usage: ws6 rebase {workspace_name} [force]"
    echo "Usage: ws6 finish {workspace_name} [done-all]"
    echo "rebase: rebase the workspace to establish the correct overlay, if force is provided, rebuild the workspace"
    echo "start: start the workspace, pull git repo, activate conda env and apply patch"
    echo "finish: finish the workspace, export changes, if done-all is provided, delete git repo metadata"
}

main $@
