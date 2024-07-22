#!/usr/bin/env python3 
import time
import numpy as np
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

def main():
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
    prev = None
    encoding = False
    filestem = None
    request = None
    ltime = 0
    mse_thresh = 22

    time_between_motion = 6.0 # min length of video, in seconds

    while True:
        cur = picam2.capture_buffer("lores")
        cur = cur[:w * h].reshape(h, w)
        if prev is not None:
            # Measure pixel differences between current and previous frame
            mse = np.square(np.subtract(cur, prev)).mean()
            
            if mse > mse_thresh:
                if not encoding:
                    filestem = time.strftime("%Y%m%d-%H%M%S")
                    print(f"New motion {mse} over threshold {mse_thresh}")
                    request = picam2.capture_request()
                    request.save("main", f"{filestem}.jpg")
                    print(f"preview saved to {filestem}.jpg")

                    filename = f"{filestem}.mp4"
                    print(f"start recording to {filename}")
                    encoder.output = FfmpegOutput(filename)
                    picam2.start_encoder(encoder)
                    encoding = True

                ltime = time.time()
            else:
                if encoding and time.time() - ltime > time_between_motion:
                    picam2.stop_encoder()
                    print(f"stop recording to {filename}")
                    encoding = False
                    filestem= None
                    request.release()
        prev = cur


if __name__ == "__main__":
    main()