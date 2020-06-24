#!/usr/bin/env bash
# ------------------------------------------------------------------------------
#
# Copyright (c) 2020 Marcin Sielski.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# ------------------------------------------------------------------------------

if [ "x$1" == "x--debug" ]; then

python3 main.py -i "nvarguscamerasrc ! video/x-raw(memory:NVMM), width=(int)768, height=(int)432,format=(string)NV12, framerate=(fraction)10/1 ! nvvidconv ! video/x-raw, format=(string)I420 ! appsink" -m model/ssdlite_mobilenet_v2.xml -d MYRIAD -pt 0.3 -g yes

else

OPENCV_LOG_LEVEL=SILENT python3 main.py -i "nvarguscamerasrc ! video/x-raw(memory:NVMM), width=(int)768, height=(int)432,format=(string)NV12, framerate=(fraction)10/1 ! nvvidconv ! video/x-raw, format=(string)I420 ! appsink" -m model/ssdlite_mobilenet_v2.xml -d MYRIAD -pt 0.3 | ffmpeg -v warning -f rawvideo -pixel_format bgr24 -video_size 768x432 -framerate 24 -i - http://0.0.0.0:3004/fac.ffm

fi
