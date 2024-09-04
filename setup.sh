#!/bin/sh
echo "Install systemd service for TinyCam"
mkdir -p $HOME/.config/systemd/user/
mkdir -p $HOME/tinycam/images/
cp tinycam.service $HOME/.config/systemd/user/

echo "Enable and start TinyCam"
systemctl --user enable tinycam
systemctl --user start tinycam

echo "Enable user process lingering for $USER"
loginctl enable-linger

systemctl --user status tinycam

echo "To see the status of the tinycam service, run 'systemctl --user status tinycam'"
echo "To see logs for the tinycam service, run 'journalctl --user -u tinycam.service'"