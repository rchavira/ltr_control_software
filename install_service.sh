cp ./control_software.service /lib/systemd/system/control_software.service
systemctl daemon-reload
systemctl enable control_software.service
systemctl start control_software.service
