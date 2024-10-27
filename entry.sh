#!/bin/bash

source config.cfg.sh

# rebase workspace to correct overlay, $1 is the workspace name
function rebase() {
    # $_WS6_PY check-workspace $1


    unset ROS_PACKAGE_PATH
    $_WS6_PY prepare-list $1 && source $_SOURCE_LIST
    if [ $? -ne 0 ]; then
        echo -e "\e[31m Error check workspace $1 \e[0m"
        return 1
    fi
    if [[ "$1" == "$_ROS" ]]; then
        echo -e "\e[32m Successfully rebase workspace $1 \e[0m"
        return 0
    fi
    # below may rebuild target workspace to form correct overlay
    pkg_count=$(echo "$ROS_PACKAGE_PATH" | awk -F':' '{print NF}')
    echo "ROS_PACKAGE_PATH num split: " $pkg_count
    if [[ "$1" == "$_WPB" ]]; then
        if [ $pkg_count -ne 2 ]; then
            # TODO: deactivate conda env
            rebase $_ROS    # Check carefully: recursive call
            pushd $_WS_ROOT/$_WPB && rm -rf devel build && catkin_make && popd
            $_WS6_PY prepare-list $_WPB && source $_SOURCE_LIST
            # TODO: restore conda env
        fi
    else
        if [ $pkg_count -ne 3 ]; then
            rebase $_WPB    # Check carefully: recursive call
            pushd $_WS_ROOT/$1 && rm -rf devel build && catkin_make && popd
            $_WS6_PY prepare-list $1 && source $_SOURCE_LIST
        fi
    fi
    echo -e "\e[32m Successfully rebase workspace $1 \e[0m"
}


function start() {
    $_WS6_PY start_p1 $1
    $_WS6_PY start_p2 $1
    # p3: activate/create conda env (conda name forced to be same as workspace name) and update environemt by env.yml

    # p4: catkin_make
    pushd $_WS_ROOT/$1 && catkin_make && popd
    # p5: rebase workspace
    rebase $1
}


function finish() {
    # p1: prepare conda env.yml
    $_WS6_PY finish_p2 $1
    # p3: deactivate conda env or change to base

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
            rebase $2
            ;;
        "start")
            start $2
            ;;
        "finish")
            finish $2
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