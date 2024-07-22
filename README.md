# TinyCam Camera
This is the camera portion of my TinyCam software. It uses the excellent [Picamera2 Library] to access the camera, which offers much higher quality and lower resource utilization than I have seen from other solutions. There is a streaming server which simply streams video from the camera. There is also a motion capture server which captures video in response to motion, with a preview image.

## Hardware
TinyCam requires a Raspberry Pi and an official Raspberry Pi Camera module. I have personally tested it on rpi 3b+, 4, 5, and zero w 1.1 with camera modules v2.1 and v3.0, both IR and noIR versions. I have tested it on 64 bit versions of Raspberry Pi on all of these models.

## Optional Software
Everyone has their own preferences for software to use on the Raspberry Pi. I usually access my pi devices via ssh and use screen to manage sessions. I use Vim as my editor. Feel free to use my public dotfiles if you don't have your own setup already.
[Screen Cheat Sheet]
[Vim Cheat Sheet]
`sudo apt install -y vim screen`
`git clone https://github.com/sweetcheetah/dotfiles.git`
`cp dotfiles/.screenrc ~`

## Software
Recent version of Raspberry Pi OS (Lite recommended)
`sudo apt update && sudo apt upgrade -y`
`sudo apt install -y git ffmpeg python3-picamera2`

## Test your setup
Once you have the prerequisites installed, test that your Raspberry Pi can access the camera by running
`rpicam-hello`

You will see output similar to the following:

```
[1:02:43.794509002] [4812]  INFO Camera camera_manager.cpp:313 libcamera v0.3.0+65-6ddd79b5
[1:02:43.940066198] [4817]  WARN RPiSdn sdn.cpp:40 Using legacy SDN tuning - please consider moving SDN inside rpi.denoise
[1:02:43.943657409] [4817]  INFO RPI vc4.cpp:446 Registered camera /base/soc/i2c0mux/i2c@1/imx708@1a to Unicam device /dev/media1 and ISP device /dev/media2
[1:02:43.943769741] [4817]  INFO RPI pipeline_base.cpp:1104 Using configuration file '/usr/share/libcamera/pipeline/rpi/vc4/rpi_apps.yaml'
Made DRM preview window
Mode selection for 2304:1296:12:P
    SRGGB10_CSI2P,1536x864/0 - Score: 3400
    SRGGB10_CSI2P,2304x1296/0 - Score: 1000
    SRGGB10_CSI2P,4608x2592/0 - Score: 1900
[1:02:44.050737301] [4812]  INFO Camera camera.cpp:1183 configuring streams: (0) 2304x1296-YUV420 (1) 2304x1296-SBGGR10_CSI2P
[1:02:44.051357962] [4817]  INFO RPI vc4.cpp:621 Sensor: /base/soc/i2c0mux/i2c@1/imx708@1a - Selected sensor format: 2304x1296-SBGGR10_1X10 - Selected unicam format: 2304x1296-pBAA
```

If you see an error or a message that no cameras were found, you have a problem with your hardware or software setup.

## Install TinyCam
The best way to install TinyCam is to clone the git repo and set it up to run as a systemd service.

Start by cloning the repo.
`git clone https://github.com/sweetcheetah/tinycam.git`
Change into the tinycam directory.
`cd tinycam`
Run the motion camera manually to make sure everything is working properly to this point.
~/tinycam `python motion.py`

You should see messages similar to the following:
```
```

And when there is motion in front of the camera lens, messages like this:
```
```

Press control-c to exit the motion camera. You are now ready to install the camera to run as a systemd service.

`./setup.sh`

## Monitor
`systemctl --user status tinycam`
`journalctl --user -u tinycam.service`