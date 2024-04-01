# fanpidctrl
Use IPMI to control the fans of some Supermicro boards.
>[!NOTE]
>The default setting try to keep the temperature areound 60C
it could be set by `-t [temperature]`

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
