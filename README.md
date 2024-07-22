# TinyCam Camera

## Why TinyCam?

## Hardware

## Software
Recent version of Raspberry Pi OS (Lite recommended)
`sudo apt update && sudo apt upgrade -y`
`sudo apt install -y git ffmpeg python3-picamera2`

## Optional Software
`sudo apt install -y vim screen`
git clone https://github.com/sweetcheetah/dotfiles.git
cp dotfiles/.screenrc ~

## Test your setup
`rpicam-hello`
~/tinycam `python motion.py`

## Install TinyCam
`git clone https://github.com/sweetcheetah/tinycam.git`
`cd tinycam`
`./setup.sh`

## Monitor
`systemctl --user status tinycam`
`journalctl --user -u tinycam.service`