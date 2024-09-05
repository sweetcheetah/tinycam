#!/usr/bin/env python3
"""A simple streaming mjpg server"""

from streaming import StreamingOutput, StreamingServer, StreamingHandler

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput

picam2 = Picamera2() # pylint: disable=not-callable
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()
picam2.start_recording(MJPEGEncoder(), FileOutput(output))

try:
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    picam2.stop_recording()
