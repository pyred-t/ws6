# s6
for ros workspace management

1. use ps1 to show ros_package_path, e.g. *m@LAPTOP[wpb_ws;noetic]:~/s6$*
note: catkin_make 时会将当前的环境变量 ros_package_path 进行记录，如果此时环境变量为空，则执行 source devel/setup.sh 后的 ros_package_path 仅有当前 workspace，否则会使 make 前的环境变量拼接当前的 workspace。
