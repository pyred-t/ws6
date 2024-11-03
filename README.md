# ws6
for ros workspace management associated with wpb
![image](https://github.com/user-attachments/assets/45a724dc-9529-421a-bf37-e2143597b898)

## Usage
### 环境需求

1. conda
2. python click

### Install

```bash
git clone this-repo.git
cd ws6 && ./scripts/install.sh
source ~/.bashrc
```

### 流程
0. 准备一个 git 项目仓库

1. 开始/继续一个新的工作区

```bash
ws6 start {workspace_name}
```
将会创建/定位到对应工作区目录，从 git 中拉取代码，将 pach 文件应用到 wpb 中，自动创建一个新分支`{dev}-{ws}-{time}`；并创建/激活(按 env.yml ) conda 环境，重新编译工作区

如果在编译中失败了，解决问题后使用 `rebase {workspace} y` 重新编译即可

2. 结束当前开发

```bash
ws6 finish {workspace_name}
ws6 finish {workspace_name} y
```
将会生成 conda 环境依赖到工作目录下 env.yml， 将 wpb 所有改动打包至工作目录下的 external 目录下

如果设置了 y 参数 (done-all-yes)，将会执行提交代码的操作，成功后删除工作目录 .git/ 元信息，rebase 至 noetic

3. optional: rebase
```bash
ws6 rebase {workspace}
ws6 rebase {workspace} y
```
定位至目标工作目录，构建 overlay (即 workspace-wpb-noetic)，如果设置了 y 参数 (force)，将会执行重新编译操作。

### 配置
相关配置在 config.cfg.sh 目录下，主要针对路径等。


## 思路
使用点命令(. or source)执行脚本，以使得环境变量在本终端生效

---
Use `PS1` to show \$ros_package_path, *e.g. m@LAPTOP[wpb_ws;noetic]:~/s6$*

note1:\
在工作空间执行 catkin_make 时会将当前的环境变量 ros_package_path 进行记录，如果此时环境变量为空，则执行 *source devel/setup.sh* 后的 ros_package_path 仅有当前 workspace，否则为 catkin_make 前的环境变量拼接当前的 workspace

note2:\
*source devel/setup.sh* 后的 ros_package_path 在初次 catkin_make 时就已确定，将在删除 build/devel 下的内容重新 catkin_make 后才重新确定

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
