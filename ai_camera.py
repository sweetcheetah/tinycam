#!/usr/bin/env python3
"""Use imx500 raspberry pi ai camera to look for events and record a poster image + video
 for as long as the event lasts.
An event is an object detection that has not been excluded by configuration. 
An event triggers an image capture and triggers a video capture that lasts until 
only excluded objects are in frame.
Once the video capture concludes, the event is sent to the local tinycam-ui API to tag 
the video and poster image
configuration options:
path for ml model
API server (e.g. http://localhost:3000), should not include path
excluded tags
"""
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
from picamera2.devices import IMX500
from picamera2.devices.imx500 import (NetworkIntrinsics,postprocess_nanodet_detection)

from dataclasses import dataclass
from typing import List
import logging
import sys
import os
import numpy as np
import time
import requests
from functools import lru_cache

last_detections = []
encoder = H264Encoder(1000000)


# ENV VARS
model: str = os.getenv('MODEL',"/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk")
thresh: str = os.getenv('TINYCAM_THRESHOLD', '0.55')
images_dir: str = os.getenv('IMAGES_DIR',".")
api_server: str = os.getenv('API_SERVER',"http://localhost:3000")
excluded_tags: str = os.getenv('EXCLUDED_TAGS','')
min_capture_seconds: str = os.getenv('TINYCAM_MIN_VIDO_LEN','10')


class Detection:
    """Class to encapsulate an object detection from the imx500"""
    def __init__(self, coords, category, conf, metadata):
        """Create a Detection object, recording the bounding box, category and confidence."""
        self.category = category
        self.conf = conf
        self.box = imx500.convert_inference_coords(coords, metadata, picam2)
        self.source = f"ai:{model}"

    def __repr__(self):
        labels = get_labels()
        return f"{type(self).__name__}(category='{labels[int(self.category)]}', confidence={self.conf:.2f})"


class Capture:
    """A video capture class to encapsulate data and state around a capture."""
    def __init__(self,asset_id):
        self.asset_id: str = asset_id
        self.is_capturing: bool = False
        self.poster = None
        self.start: float = None
        self.tags: List[Tag] = []

    def stop(self) -> None:
        picam2.stop_encoder()
        logging.info("Stop recording")
        self.tag()

    def tag(self) -> None:
        """POST self.tags to tagging API"""
        # TODO test
        path: str = "/api/tags"
        url: str = f"{api_server}{path}"
        unique_tags = list(set([t.tag for t in self.tags]))
        unique_tags_list = [ Tag(asset_id=self.asset_id, tag=t) for t in unique_tags]

        requests.post(url, data=unique_tags_list)
        r = requests.post(url=url,json=unique_tags_list)

        logging.info(r.status_code)
        logging.info(r.json())
    

    def update_tags(self,detections: List[Detection]) -> None:
        """Add tags to this Capture"""
        for detection in detections:
            logging.info(f"detection: {detection}")
            self.tags.append(Tag(asset_id=self.asset_id,tag=detection.category))

    def start_or_continue(self,request,filestem: str) -> None:
        if not self.is_capturing:
            self.is_capturing = True
            self.start = time.monotonic()
            filestem = time.strftime("%Y%m%d-%H%M%S")
            
            # capture poster 
            logging.info("Save preview to %s.jpg", filestem)
            request.save("main", f"{images_dir}/{filestem}.jpg")
            
            # start video capture
            filename = f"{filestem}.mp4"
            logging.info("Start recording to %s", filename)
            encoder.output = FfmpegOutput(f"{images_dir}/{filename}")
            picam2.start_encoder(encoder)

@dataclass
class Tag:
  asset_id: str
  tag: str
  camera: str = os.getenv('CAMERA_NAME', 'tinycam')
    
            
@lru_cache
def get_labels() -> List[str]:
    labels = intrinsics.labels

    if intrinsics.ignore_dash_labels:
        labels = [label for label in labels if label and label != "-"]
    return labels

def remove_excluded(detections: List[Detection]):
    """Remove tags that have been excluded from the list of detected tags"""
    remaining = detections
    for d in remaining:
        tag = get_labels()[int(d.category)]
        if tag in excluded_tags:
            remaining.remove(d)
    
    return remaining

    
def parse_detections(metadata: dict) -> List[Detection]:
    """Parse the output tensor into a number of detected objects, scaled to the ISP output."""
    logging.debug('parse_detections')
    global last_detections
    bbox_normalization = intrinsics.bbox_normalization
    bbox_order = intrinsics.bbox_order
    threshold = float(thresh)
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
    imx500 = IMX500(model)
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
        buffer_count=12, # camera will freeze if it runs out of buffers
        main={"size": high_size, "format": "RGB888"},
        lores={"size": low_size, "format": "YUV420"}
    )

    #imx500.show_network_fw_progress_bar()
    picam2.start(config)

    if intrinsics.preserve_aspect_ratio:
        imx500.set_auto_aspect_ratio()

    last_results = None
    asset_capture = None

    while True:
        last_results = parse_detections(picam2.capture_metadata())
        last_results = remove_excluded(last_results)

        if len(last_results) > 0:
            logging.debug(f"last_results: {last_results}")
            request = picam2.capture_request()
            filestem = time.strftime("%Y%m%d-%H%M%S")
            if not asset_capture:
                asset_capture = Capture(filestem)
            asset_capture.start_or_continue(request, filestem)
            asset_capture.update_tags(last_results)
            request.release()
        else:
            if asset_capture and asset_capture.is_capturing is True:
                if time.monotonic() - asset_capture.start > float(min_capture_seconds):
                    asset_capture.stop()
                    asset_capture = None

