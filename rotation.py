"""Utility module to rotate picamera video by the given degrees"""
import libcamera

def transform(rotation: int) -> libcamera.Transform:
    """Pass one of three supported rotations(90,180 or 270). Returns a libcamera.Transform object."""
    transform: libcamera.Transform|None = None

    if rotation == 90:
        transform = libcamera.Transform(hflip=True, transpose=True)
    elif rotation == 180:
        transform = libcamera.Transform(hflip=True, vflip=True)
    elif rotation == 270:
        transform = libcamera.Transform(transpose=True)

    return transform
