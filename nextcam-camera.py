#!/usr/bin/python3

import time
import numpy as np
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

high_size = (1280,720)
low_size = (320, 240)
picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={"size": high_size, "format": "RGB888"},
                                                 lores={"size": low_size, "format": "YUV420"})
picam2.configure(video_config)
encoder = H264Encoder(1000000)
picam2.start()

# TODO threshhold, min_movie_length should be env vars
# TODO factor some stuff out into functions

w, h = low_size
prev = None
encoding = False
filestem = None
request = None
ltime = 0
mse_thresh = 22

time_between_motion = 6.0 # in seconds

while True:
    cur = picam2.capture_buffer("lores")
    cur = cur[:w * h].reshape(h, w)
    if prev is not None:
        # Measure pixels differences between current and
        # previous frame
        mse = np.square(np.subtract(cur, prev)).mean()
        #print(f"mse: {mse}")
        if mse > mse_thresh:
            if not encoding:
                filestem = time.strftime("%Y%m%d-%H%M%S")
                filename = f"{filestem}.mp4"
                #filename = datetime.datetime.now().isoformat().replace(':','')
                print(f"start recording to {filename}")
                encoder.output = FfmpegOutput(filename)
                picam2.start_encoder(encoder)
                encoding = True
                print(f"New Motion {mse} over threshold {mse_thresh}")
                #print("capture preview image")
                request = picam2.capture_request()
                request.save("main", f"{filestem}.jpg")
                print(f"preview saved to {filestem}.jpg")
            ltime = time.time()
        else:
            if encoding and time.time() - ltime > time_between_motion:
                picam2.stop_encoder()
                print(f"stop recording to {filename}")
                encoding = False
                filestem= None
                request.release()
    prev = cur

