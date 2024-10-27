# ws6
for ros workspace management

---
使用点命令(. or source)执行脚本，以使得环境变量在本终端生效


---
Use `PS1` to show \$ros_package_path, *e.g. m@LAPTOP[wpb_ws;noetic]:~/s6$*

note1:\
在工作空间执行 catkin_make 时会将当前的环境变量 ros_package_path 进行记录，如果此时环境变量为空，则执行 *source devel/setup.sh* 后的 ros_package_path 仅有当前 workspace，否则为 catkin_make 前的环境变量拼接当前的 workspace

~~note2:\
*source devel/setup.sh* 后的 ros_package_path 在初次 catkin_make 时就已确定，将在删除 build/devel 下的内容重新 catkin_make 后才重新确定~~

---
Use miniforge to manage python virtual environment\
*conda config --set auto_activate_base false*

note1:\
Python 模块默认搜索路径：Python 在启动时会根据一系列规则自动设置模块搜索路径(import sys; sys.path)，按序包括：
- 当前工作目录
- 环境变量 PYTHONPATH 指定的目录 /opt/ros/noetic/lib/python3/dist-packages
- Python 标准库的路径（通常是安装时的 lib 目录）
- 第三方库的路径（如在 site-packages 目录中的库） 

note2:\
每个新创建环境，需要 pip 安装依赖 catkin-tools, rosdep, empy

note3:\
初次 catkin_make 或清除 build 下的内容重新执行 catkin_make 会自动识别使用当前环境的 python 解析器\
如果想直接重新 catkin_make, 执行 *catkin_make -DPYTHON_EXECUTABLE=$(which python)*\
catkin 会记录这次编译的解释器位置，并在以后运行时使用该解析器。

note4:\
测试 talker.py, listener.py 可正常运行的 python 版本(Noetic target for python 3.8):

| 版本 | Y/N | 
| --- | --- |
| 3.8.20 | Y |
| 3.9.20 | Y |
| 3.10.15 | Y | 
| 3.12.7 | N |  


---
Use git to manage code

note1:\
为防止各组代码库泄露，不允许使用基于 SSH Keys 的访问方式，使用基于 Personal Access Token 的 HTTP(S) 方式初始化代码库

note2:\
对于公共包的修改打包成 .patch, 对于 conda 的环境生成 requirement.txt, 一起在结束时 push 至远程代码库新分支\
*git format-patch origin/master..HEAD`*\
*git format-patch origin/master..HEAD --stdout > all_commits.patch*\
*git am \*.patch*\
*conda env export > environment.yml*\
*conda env update -f environment.yml*
