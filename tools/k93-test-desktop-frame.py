#!/usr/bin/env python3
"""Actual framebuffer-capture decoder checks; synthetic data, no display."""
import base64
import gzip
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('frame',Path(__file__).with_name('k93-extract-desktop-frame.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ppm=m.HEADER+bytes(1024*768*3)
def log(data):
    return ('K93_DESKTOP_PROCESSES_ALIVE\nK93_FB_PPM_BEGIN\n'+
            base64.b64encode(gzip.compress(data)).decode()+'\nK93_FB_PPM_END\n'+
            'K93_FB_READ 1024x768 bpp32 stride4096 RGB16/8/0\n'+
            'K93_DESKTOP_END\nK93_DESKTOP_CLEANUP\nDESKTOP_EXIT=0\n')
valid='\n'+log(ppm)
assert m.decode(valid)==ppm
for invalid in [valid.replace('DESKTOP_EXIT=0','DESKTOP_EXIT=1'),
                valid.replace('K93_DESKTOP_PROCESSES_ALIVE','missing'),
                '\n'+log(ppm+b'x'), '\n'+log(ppm[1:]),
                valid.replace('1024x768 bpp32','wrong framebuffer mode'),
                valid+'\nK93_FB_PPM_BEGIN\n']:
    try:m.decode(invalid)
    except (AssertionError,ValueError):pass
    else:raise AssertionError('Incomplete/oversized frame accepted')
print('PASS: actual decoder validates desktop markers, bounded gzip/PPM dimensions and rejects failures; no visual success inferred')
