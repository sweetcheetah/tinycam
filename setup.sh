#!/bin/sh
echo "Install prerequisites"
sudo apt install ffmpeg python3-picamera2 python3-opencv opencv-data

# AI Camera
if [$1 = "ai"]; then
    sudo apt install -y imx500-all
    sudo apt install -y python3-munkres
fi

echo "Install systemd service for TinyCam"
mkdir -p $HOME/.config/systemd/user/
mkdir -p $HOME/tinycam/images/

if [$1="ai"]; then
    cp ai_tinycam.service $HOME/.config/systemd/user/tinycam.service
else
    cp tinycam.service $HOME/.config/systemd/user/

echo "Enable and start TinyCam"
systemctl --user enable tinycam
systemctl --user start tinycam

echo "Enable user process lingering for $USER"
loginctl enable-linger

systemctl --user status tinycam

echo "To see the status of the tinycam service, run 'systemctl --user status tinycam'"
echo "To see logs for the tinycam service, run 'journalctl --user -u tinycam.service'"