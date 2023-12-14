#!/bin/bash

# ping百度一次
ping -c 1 www.baidu.com > /dev/null 2>&1

# 检查上一个命令的退出状态
if [ $? -ne 0 ]; then
    echo "无法连接到百度"
    python3 buaa_gateway_login.py
    # 在这里放置你想要执行的命令

fi