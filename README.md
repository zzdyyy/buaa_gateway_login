# 北航校园网登录脚本

北航校园网登录网址gw.buaa.edu.cn采用了SRun深澜认证计费系统，本项目buaa_gateway_login.py提供了最小化登录脚本，直接运行即可在控制台模拟Web端的登录。

# 配置自动登录脚本

以下步骤展示在Linux中通过systemd配置断网检测和自动登录服务。

首先，将登录信息写入buaa_gateway_login.py中，并将其保存到`/usr/local/bin/buaa_gateway_login.py`。

```python
...
if __name__ == "__main__":

    username = 'by1234567'
    password = 'password'
...
```

第二步，编写断网检测代码`/usr/local/bin/buaa_gateway_login.sh`如下。这个脚本使用百度来检测网络连接，在断网时尝试登录，网络正常时什么也不做。

```bash
#!/usr/bin/env bash
# 如果校园网未登录，访问百度将会跳转到gw.buaa.edu.cn
if curl -s www.baidu.com 2>/dev/null | grep gw.buaa.edu.cn >/dev/null 2>&1; then
    python3 /usr/local/bin/buaa_gateway_login.py
fi
```

第三步，给以上重连脚本增加可执行权限，并包装成systemd服务：编辑`/etc/systemd/system/buaa_gateway_login.service`如下

```conf
[Unit]
Description=Automatically relogin when gateway logged out.

[Service]
Type=oneshot
ExecStart=/usr/local/bin/buaa_gateway_login.sh
User=nobody
Group=systemd-journal
```

此时即可通过`systemctl start buaa_gateway_login.service`来进行一次自动登录。

第四步，为上述服务设置定时器`/etc/systemd/system/buaa_gateway_login.timer`，下面的OnCalendar设置为每隔10分钟执行一次。

```conf
[Unit]
Description=Automatically relogin when gateway logged out.

[Timer]
OnCalendar=*-*-* *:0/10:0
Persistent=true

[Install]
WantedBy=timers.target
```

最后只需要启动计时器即可

```bash
sudo systemctl enable buaa_gateway_login.timer  # 开机自动启动
sudo systemctl start buaa_gateway_login.timer   # 立即开始
```

为了保证安全，以上文件属主全部设为root。

