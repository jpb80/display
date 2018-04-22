
apt update
apt install python3

# Remove unncessary packages to maximize pi performance
apt remove bluez bluez-firmware pi-bluetooth triggerhappy pigpio

pip3 install -r requirements.txt

cat <<EOF | sudo tee /etc/modprobe.d/blacklist-rgb-matrix.conf
blacklist snd_bcm2835
EOF
update-initramfs -u

reboot 1

echo 'Rebooting...'

