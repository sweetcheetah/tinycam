# TinyCam Camera
This is the camera portion of my TinyCam software. It uses the excellent [Picamera2 Library](https://github.com/raspberrypi/picamera2) to access the camera, which offers much higher quality and lower resource utilization than other solutions. There is a streaming server which simply streams video from the camera. There is also a motion capture server which captures video in response to motion, with a preview image.

## Hardware
TinyCam requires a Raspberry Pi and an official Raspberry Pi Camera module. I have tested it on rpi 3b+, 4, 5, and zero w 1.1 with camera modules v2.1 and v3.0, both normal and noIR versions. I have tested it on 64 bit versions of Raspberry Pi on all of these models.

## Optional Software
Everyone has their own preferences for software to use on the Raspberry Pi. I usually access my pi devices via ssh and use screen to manage sessions. This gives you the ability to keep your terminal sessions open even when your ssh connection drops. I use Vim as my editor. Feel free to use my public dotfiles if you don't have your own setup already.

[Screen Cheat Sheet](https://devhints.io/screen)
[Vim Cheat Sheet](http://vimsheet.com/)

Install vim and screen.
```sh
sudo apt install -y vim screen
```

Clone dotfiles from my repo.
```sh
git clone https://github.com/sweetcheetah/dotfiles.git
```

Copy dotfiles to your home directory.
```sh
cp dotfiles/.screenrc ~
```

## Software
Recent version of Raspberry Pi OS (Lite recommended)
Update your OS.
```sh
sudo apt update && sudo apt upgrade -y
```

Install prerequisite software.
```sh
sudo apt install -y git ffmpeg python3-picamera2
```

## Test your setup
Once you have the prerequisites installed, test that your Raspberry Pi can access the camera by running
```sh
rpicam-hello
```

You will see output similar to the following:

```sh
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
```sh
git clone https://github.com/sweetcheetah/tinycam.git
```

Change into the tinycam directory.
```sh
cd tinycam
```

Run the motion camera manually to make sure everything is working properly to this point.
```sh
python motion.py
```

You should see messages similar to the following:
```sh
[47:01:59.867601119] [7992]  INFO Camera camera_manager.cpp:313 libcamera v0.3.0+65-6ddd79b5
[47:01:59.979183558] [7995]  WARN RPiSdn sdn.cpp:40 Using legacy SDN tuning - please consider moving SDN inside rpi.denoise
[47:01:59.981373432] [7995]  INFO RPI vc4.cpp:446 Registered camera /base/soc/i2c0mux/i2c@1/imx708@1a to Unicam device /dev/media1 and ISP device /dev/media2
[47:01:59.981449913] [7995]  INFO RPI pipeline_base.cpp:1104 Using configuration file '/usr/share/libcamera/pipeline/rpi/vc4/rpi_apps.yaml'
[47:01:59.983979841] [7992]  INFO Camera camera_manager.cpp:313 libcamera v0.3.0+65-6ddd79b5
[47:02:00.110780404] [7998]  WARN RPiSdn sdn.cpp:40 Using legacy SDN tuning - please consider moving SDN inside rpi.denoise
[47:02:00.112776169] [7998]  INFO RPI vc4.cpp:446 Registered camera /base/soc/i2c0mux/i2c@1/imx708@1a to Unicam device /dev/media1 and ISP device /dev/media2
[47:02:00.112850501] [7998]  INFO RPI pipeline_base.cpp:1104 Using configuration file '/usr/share/libcamera/pipeline/rpi/vc4/rpi_apps.yaml'
[47:02:00.119901826] [7992]  INFO Camera camera.cpp:1183 configuring streams: (0) 1280x720-RGB888 (1) 320x240-YUV420 (2) 1536x864-SBGGR10_CSI2P
[47:02:00.120402619] [7998]  INFO RPI vc4.cpp:621 Sensor: /base/soc/i2c0mux/i2c@1/imx708@1a - Selected sensor format: 1536x864-SBGGR10_1X10 - Selected unicam format: 1536x864-pBAA
```

And when there is motion in front of the camera lens, messages like this:
```sh
New motion 47.46110677083333 over threshold 22
preview saved to 20240724-121740.jpg
start recording to 20240724-121740.mp4
stop recording to 20240724-121740.mp4
```

Press control-c to exit the motion camera. You are now ready to install the camera to run as a systemd service.

First, make the setup script executable.

```sh
chmod +x ~/tinycam/setup.sh
```

```sh
./setup.sh
```

Congratulations! TinyCam is now running as a user systemd service. It will start automatically when the pi boots, and save video and images to the images directory under your home directory.

## Monitor
You can see the current status of the TinyCam service by running:
```sh
systemctl --user status tinycam
```

You can see the logs for the service by running:
```sh
journalctl --user -u tinycam.service
```