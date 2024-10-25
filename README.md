# s6
for ros workspace management

---
use `PS1` to show \$ros_package_path, *e.g. m@LAPTOP[wpb_ws;noetic]:~/s6$*

note1:\
在工作空间执行 catkin_make 时会将当前的环境变量 ros_package_path 进行记录，如果此时环境变量为空，则执行 *source devel/setup.sh* 后的 ros_package_path 仅有当前 workspace，否则为 catkin_make 前的环境变量拼接当前的 workspace

~~note2:\
*source devel/setup.sh* 后的 ros_package_path 在初次 catkin_make 时就已确定，将在删除 build/devel 下的内容或 *catkin_make clean* 后重新 catkin_make 之后才重新确定~~

