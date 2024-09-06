#!/usr/bin/env python3
"""TinyCam"""
import time
import os
#import threading
import logging
from rotation import add_rotation
import numpy as np
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

from systemd import Notify
#import streaming


def main():
    """Main method to start the camera"""
    #streaming_server = streaming.TinyCamStreamingServer()
    notify: Notify = Notify()

    if notify.enabled():
        notify.status("Initializing TinyCam")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s'
    )

    # environment
    mse_thresh: int = int(os.getenv('TINYCAM_THRESHOLD', "9"))
    min_video_length: float = float(os.getenv('TINYCAM_MIN_VIDEO_LEN',"10.0"))
    trigger_frames: int = int(os.getenv('TINYCAM_TRIGGER',"3"))
    rotation: int = int(os.getenv('TINYCAM_ROTATION',"0"))

    high_size = (1280,720)
    low_size = (320, 240)
    picam2 = Picamera2() # pylint: disable=not-callable

    video_config = picam2.create_video_configuration(
        main={"size": high_size, "format": "RGB888"},
        lores={"size": low_size, "format": "YUV420"}
    )

    if rotation != 0:
        video_config["transform"] = rotation.transform(rotation)

    picam2.configure(video_config)
    encoder = H264Encoder(1000000)
    picam2.start()

    w, h = low_size
    previous_frame = None
    #reference_frame = None
    encoding = False
    filestem = None
    request = None
    ltime = 0
    trigger_count = 0


    # TODO: refine this
    # 1. streaming
    # 2. retain original frame before motion to compare against instead of the prev frame
    while True:
        current_frame = picam2.capture_buffer("lores")
        current_frame = current_frame[:w * h].reshape(h, w)

        if notify.enabled():
            notify.ready()

        #streaming_server.input_frame(current_frame)

        if previous_frame is not None:
            # Measure pixel differences between current and previous frame
            mse: float = np.square(np.subtract(current_frame, previous_frame)).mean()

            if mse > mse_thresh:
                trigger_count = trigger_count + 1
                if trigger_count > trigger_frames:
                    if not encoding:
                        filestem = time.strftime("%Y%m%d-%H%M%S")
                        logging.info("New motion %f over threshold %i", mse, mse_thresh)
                        request = picam2.capture_request()
                        request.save("main", f"{filestem}.jpg")
                        logging.info("Preview saved to %s.jpg", filestem)

                        filename = f"{filestem}.mp4"
                        logging.info("Start recording to %s", filename)
                        encoder.output = FfmpegOutput(filename)
                        picam2.start_encoder(encoder)
                        encoding = True

                    ltime = time.time()
            else:
                if encoding and time.time() - ltime > min_video_length:
                    picam2.stop_encoder()
                    logging.info("Stop recording to %s", filename)
                    encoding = False
                    filestem= None
                    request.release()
        previous_frame = current_frame

        if notify.enabled():
            notify.notify()



if __name__ == "__main__":
    main()
