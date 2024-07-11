# TinyCam Camera
## install prereqs for camera
Recent version of Raspberry Pi OS
`sudo apt update && sudo apt upgrade -y`
`sudo apt install -y ffmpeg`

## RUN camera under systemd
First make sure the camera is recognized by running the camera app manually.
`python motion.py`
Ctrl-C to exit
