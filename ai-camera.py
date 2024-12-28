#!/usr/bin/env python3
"""Use imx500 raspberry pi ai camera to look for events and record a poster image + video for as long as the event lasts."""
from picamera2 import MappedArray, Picamera2
from picamera2.devices import IMX500
from picamera2.devices.imx500 import (NetworkIntrinsics,
                                      postprocess_nanodet_detection)
import logging
import sys
import numpy as np
import time
import requests


# An event is an object detection that has not been specifically excluded by configuration
# an event has a category, confidence, timestamp, and bounding box
# an event should trigger an image capture
# an event should trigger a video capture that lasts until only excluded objects are in frame
# once the video capture concludes, the event should be sent to the local tinycam-ui API to tag the video and poster image
# configuration options:
# which model to use
# API server
# excluded objects
# excluded regions

## base on picamera2/examples/imx500/imx500_object_detection_demo.py

MODEL = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"
API_SERVER = "http://localhost:5173"
EXCLUDED_OBJECTS = []
EXCLUDED_REGIONS = []

class Detection:
    def __init__(self, coords, category, conf, metadata):
        """Create a Detection object, recording the bounding box, category and confidence."""
        self.category = category
        self.conf = conf
        self.box = imx500.convert_inference_coords(coords, metadata, picam2)

    def __repr__(self):
        return f"{type(self).__name__}(category='{self.category}', confidence={self.conf})"

def parse_detections(metadata: dict):
    """Parse the output tensor into a number of detected objects, scaled to the ISP output."""
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

    # Defaults
    if intrinsics.labels is None:
        with open("assets/coco_labels.txt", "r") as f:
            intrinsics.labels = f.read().splitlines()
    intrinsics.update_with_defaults()

    picam2 = Picamera2(imx500.camera_num)
    config = picam2.create_preview_configuration(controls={"FrameRate": intrinsics.inference_rate}, buffer_count=12)

    imx500.show_network_fw_progress_bar()
    picam2.start(config, show_preview=False)

    # if intrinsics.preserve_aspect_ratio:
    #     imx500.set_auto_aspect_ratio()

    last_results = None
    # TODO: should this be done in post_callback or after encoding?
    #picam2.post_callback = collect_tags

    while True:
        last_results = parse_detections(picam2.capture_metadata())
        if len(last_results) > 0:

            # capture image
            filestem = time.strftime("%Y%m%d-%H%M%S")
            request = picam2.capture_request()
            request.save("main", f"./{filestem}.jpg")

            # log detections
            i=1
            for detection in last_results:
                category = intrinsics.labels[int(detection.category)]
                logging.info(f"{i} detected {category} ({detection.conf:.2f})")
                i += i

            time.sleep(1)
    