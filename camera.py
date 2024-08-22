#!/usr/bin/env python3
import time
import os
import logging
import numpy as np
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

from systemd import Notify

def main():
    notify: Notify = Notify()
    notify.status("Initializing TinyCam")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s'
    )

    high_size = (1280,720)
    low_size = (320, 240)
    picam2 = Picamera2()

    video_config = picam2.create_video_configuration(
        main={"size": high_size, "format": "RGB888"},
        lores={"size": low_size, "format": "YUV420"}
    )
    picam2.configure(video_config)
    encoder = H264Encoder(1000000)
    picam2.start()

    w, h = low_size
    previous_frame = None
    encoding = False
    filestem = None
    request = None
    ltime = 0
    mse_thresh = os.getenv('TINYCAM_THRESHOLD', 22)
    # min length of video, in seconds
    min_video_length = os.getenv('TINYCAM_MIN_VIDEO_LEN',10.0)
    trigger_frames = os.getenv('TINYCAM_TRIGGER',3)

    # TODO: refine this
    # 1. configurable number of frames over mse thresh
    # 2. streaming
    # 3. retain original frame before motion to compare against instead of the prev frame
    while True:
        current_frame = picam2.capture_buffer("lores")
        current_frame = current_frame[:w * h].reshape(h, w)
        if previous_frame is not None:
            # Measure pixel differences between current and previous frame
            mse = np.square(np.subtract(current_frame, previous_frame)).mean()
            
            if mse > mse_thresh:
                if not encoding:
                    filestem = time.strftime("%Y%m%d-%H%M%S")
                    logging.info(f"New motion {mse} over threshold {mse_thresh}")
                    request = picam2.capture_request()
                    request.save("main", f"{filestem}.jpg")
                    logging.info(f"preview saved to {filestem}.jpg")

                    filename = f"{filestem}.mp4"
                    logging.info(f"start recording to {filename}")
                    encoder.output = FfmpegOutput(filename)
                    picam2.start_encoder(encoder)
                    encoding = True

                ltime = time.time()
            else:
                if encoding and time.time() - ltime > min_video_length:
                    picam2.stop_encoder()
                    logging.info(f"stop recording to {filename}")
                    encoding = False
                    filestem= None
                    request.release()
        previous_frame = current_frame

        

if __name__ == "__main__":
    main()