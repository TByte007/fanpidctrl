# fanpidctrl
Use IPMI to control the fans of some Supermicro boards (tested on X11SSH-LN4F).
>[!NOTE]
>The default setting try to keep the temperature around 60C. You can change it with
`-t [temperature]` option or set it in rc.conf for example: `fanpidctrl_flags="-t 55"`.

### Simple install on FreeBSD as service
```
python -m venv venv
cd venv
. bin/activate
git clone https://github.com/TByte007/fanpidctrl.git
pip install daemonize simple-pid pyinstaller
sudo pyinstaller --onefile fanpidctrl.py --distpath /usr/local/sbin
cp rc.d/fanpidctrl /usr/local/etc/rc.d
echo 'fanpidctrl_enable="YES"' >> /etc/rc.conf
service fanpidctrl start
```
