#!/usr/bin/env python3
"""Use imx500 raspberry pi ai camera to look for events and record a poster image + video
 for as long as the event lasts."""
from picamera2 import MappedArray, Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
from picamera2.devices import IMX500
from picamera2.devices.imx500 import (NetworkIntrinsics,
                                      postprocess_nanodet_detection)
import logging
import sys
import os
import numpy as np
import time
import requests
from functools import lru_cache
import cv2

last_detections = []


# An event is an object detection that has not been specifically excluded by configuration
# an event has a category, confidence, timestamp, and bounding box
# an event should trigger an image capture
# an event should trigger a video capture that lasts until only excluded objects are in frame
# once the video capture concludes, the event should be sent to the local tinycam-ui API to tag 
# the video and poster image
# configuration options:
# which model to use
# API server
# excluded objects
# excluded regions

## based on picamera2/examples/imx500/imx500_object_detection_demo.py

MODEL = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"
images_dir: str = os.getenv('IMAGES_DIR',".")
API_SERVER = "http://localhost:5173"
EXCLUDED_OBJECTS = []
EXCLUDED_REGIONS = []

encoder = H264Encoder(1000000)

class Detection:
    """Class to encapsulate a detection from the imx500"""
    def __init__(self, coords, category, conf, metadata):
        """Create a Detection object, recording the bounding box, category and confidence."""
        self.category = category
        self.conf = conf
        self.box = imx500.convert_inference_coords(coords, metadata, picam2)

    def __repr__(self):
        labels = get_labels()
        return f"{type(self).__name__}(category='{labels[int(self.category)]}', confidence={self.conf:.2f})"
    
class Capture:
    """A video capture with poster image"""
    def __init__(self,asset_id):
        self.asset_id = asset_id
        self.is_capturing: bool = False
        self.poster = None
        self.tags: set = {}

    def start(self):
        ...

    def stop(self):
        # TODO: tag via api
        picam2.stop_encoder()
        logging.info("Stop recording")

        ...

    def continue_or_start(self,request,filestem):
        if not self.is_capturing:
            self.is_capturing = True
            filestem = time.strftime("%Y%m%d-%H%M%S")
            
            # capture poster 
            request.save("main", f"{images_dir}/{filestem}.jpg")
            logging.info("Preview saved to %s.jpg", filestem)
            
            # start video capture
            filename = f"{filestem}.mp4"
            logging.info("Start recording to %s", filename)
            encoder.output = FfmpegOutput(f"{images_dir}/{filename}")
            picam2.start_encoder(encoder)
            
@lru_cache
def get_labels():
    labels = intrinsics.labels

    if intrinsics.ignore_dash_labels:
        labels = [label for label in labels if label and label != "-"]
    return labels


def parse_detections(metadata: dict):
    """Parse the output tensor into a number of detected objects, scaled to the ISP output."""
    logging.debug('parse_detections')
    global last_detections
    bbox_normalization = intrinsics.bbox_normalization
    bbox_order = intrinsics.bbox_order
    threshold = 0.55
    iou = 0.65
    max_detections = 10

    np_outputs = imx500.get_outputs(metadata, add_batch=True)
    input_w, input_h = imx500.get_input_size()
    if np_outputs is None:
        return last_detections
    if intrinsics.postprocess == "nanodet":
        boxes, scores, classes = \
            postprocess_nanodet_detection(outputs=np_outputs[0], conf=threshold, iou_thres=iou,
                                          max_out_dets=max_detections)[0]
        from picamera2.devices.imx500.postprocess import scale_boxes
        boxes = scale_boxes(boxes, 1, 1, input_h, input_w, False, False)
    else:
        boxes, scores, classes = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0]
        if bbox_normalization:
            boxes = boxes / input_h

        if bbox_order == "xy":
            boxes = boxes[:, [1, 0, 3, 2]]
        boxes = np.array_split(boxes, 4, axis=1)
        boxes = zip(*boxes)

    last_detections = [
        Detection(box, category, score, metadata)
        for box, score, category in zip(boxes, scores, classes)
        if score > threshold
    ]
    return last_detections

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s'
    )

    # This must be called before instantiation of Picamera2
    imx500 = IMX500(MODEL)
    intrinsics = imx500.network_intrinsics

    if not intrinsics:
        intrinsics = NetworkIntrinsics()
        intrinsics.task = "object detection"
    elif intrinsics.task != "object detection":
        print("Network is not an object detection task", file=sys.stderr)
        exit()

    if intrinsics.labels is None:
        with open("assets/coco_labels.txt", "r") as f:
            intrinsics.labels = f.read().splitlines()
    intrinsics.update_with_defaults()

    high_size = (1280,720)
    low_size = (320, 240)

    picam2 = Picamera2(imx500.camera_num)
    config = picam2.create_video_configuration(
        controls={"FrameRate": intrinsics.inference_rate},
        buffer_count=12,
        main={"size": high_size, "format": "RGB888"},
        lores={"size": low_size, "format": "YUV420"}
    )

    imx500.show_network_fw_progress_bar()
    picam2.start(config, show_preview=False)

    if intrinsics.preserve_aspect_ratio:
        imx500.set_auto_aspect_ratio()

    last_results = None
    asset_capture = None

    while True:
        last_results = parse_detections(picam2.capture_metadata())

        if len(last_results) > 0:
            logging.info(f"last_results: {last_results}")
            request = picam2.capture_request()
            filestem = time.strftime("%Y%m%d-%H%M%S")
            if not asset_capture:
                asset_capture = Capture(filestem)
            asset_capture.continue_or_start(request, filestem)
            request.release()
        else:
            if asset_capture and asset_capture.is_capturing is True:
                asset_capture.stop()
                asset_capture = None

