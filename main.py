"""People Counter."""
"""
 Copyright (c) 2018 Intel Corporation.
 Permission is hereby granted, free of charge, to any person obtaining
 a copy of this software and associated documentation files (the
 "Software"), to deal in the Software without restriction, including
 without limitation the rights to use, copy, modify, merge, publish,
 distribute, sublicense, and/or sell copies of the Software, and to
 permit person to whom the Software is furnished to do so, subject to
 the following conditions:
 The above copyright notice and this permission notice shall be
 included in all copies or substantial portions of the Software.
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


import os
import sys
import time
import socket
import json
import cv2
import math

import logging as log
import paho.mqtt.client as mqtt

from argparse import ArgumentParser
from inference import Network

# MQTT server environment variables
HOSTNAME = socket.gethostname()
IPADDRESS = socket.gethostbyname(HOSTNAME)
MQTT_HOST = IPADDRESS
MQTT_PORT = 3001
MQTT_KEEPALIVE_INTERVAL = 60

def connect_mqtt():
    # Connect to the MQTT server
    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
    return client

def build_argparser():
    """
    Parse command line arguments.
    :return: command line arguments
    """
    parser = ArgumentParser()
    parser.add_argument("-m", "--model", required=True, type=str,
                        help="Path to an xml file with a trained model.")
    parser.add_argument("-i", "--input", required=True, type=str,
                        help="Path to image or video file")
    parser.add_argument("-l", "--cpu_extension", required=False, type=str,
                        default=None,
                        help="MKLDNN (CPU)-targeted custom layers."
                             "Absolute path to a shared library with the"
                             "kernels impl.")
    parser.add_argument("-d", "--device", type=str, default="CPU",
                        help="Specify the target device to infer on: "
                             "CPU, GPU, FPGA or MYRIAD is acceptable. Sample "
                             "will look for a suitable plugin for device "
                             "specified (CPU by default)")
    parser.add_argument("-pt", "--prob_threshold", type=float, default=0.55,
                        help="Probability threshold for detections filtering"
                        "(0.55 by default)")
    return parser

def make_outputs(coords, frame, in_w, in_h, x, t):
        count = 0     
        exe = x
        for i in coords[0][0]:
            if i[2] > prob_threshold:
                x_min = int(i[3] * in_w)
                y_min = int(i[4] * in_h)
                x_max = int(i[5] * in_w)
                y_max = int(i[6] * in_h)
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 0, 255), 1)
                count += 1
                let_x = frame.shape[1]/2
                let_y = frame.shape[0]/2    
                mid_x = (x_max + x_min)/2
                mid_y = (y_max + y_min)/2
                exe =  math.sqrt(math.pow(mid_x - let_x, 2) +  math.pow(mid_y - let_y, 2) * 1.0) 
                t = 0

        if count < 1:
            t += 1        
        if exe>0 and t < 10:
            count = 1 
            t += 1 
            if t > 100:
                t = 0
                
        return frame, count, exe, t

def infer_on_stream(args, client):
    # Initialise the class
    inference_network = Network()
    
    # Set Probability threshold for detections
    model=args.model
    video_file=args.input    
    extn=args.cpu_extension
    device=args.device
    single_img = False
    start_time = 0
    cur_request_id = 0
    last_count = 0
    total_count = 0
    
    # Loading of the model through `infer_network` 
    w, x, y, z = inference_network.load_model(model, device, 1, 1, cur_request_id, extn)[1]

    # Handle the input stream
    if video_file == 'CAM':
        input_stream = 0

    elif video_file.endswith('.jpg') or video_file.endswith('.bmp') :    # Check for input image
        single_img = True
        input_stream = video_file

    else:     # Check for video file
        input_stream = video_file
        assert os.path.isfile(video_file), "Specified input file doesn't exist"
    
    try:
        cap=cv2.VideoCapture(video_file)
    except FileNotFoundError:
        print("Cannot locate video file: "+ video_file)
    except Exception as e:
        print("Something else went wrong with the video file: ", e)
        
    global in_w, in_h, prob_threshold
    total_count = 0  
    duration = 0
    
    in_w = cap.get(3)
    in_h = cap.get(4)
    prob_threshold = args.prob_threshold
    temp = 0
    tk = 0
    
    # Loop until stream is over
    while cap.isOpened():
        # Read from the video capture
        flag, frame = cap.read()
        if not flag:
            break
        key_pressed = cv2.waitKey(60)
        # Pre-process of the image as needed
        image = cv2.resize(frame, (z, y))
        # Change data layout from HWC to CHW
        image = image.transpose((2, 0, 1))
        image = image.reshape((w, x, y, z))
        
        # Start asynchronous inference for specified request
        inf_start = time.time()
        inference_network.exec_net(cur_request_id, image)
        
        color = (255,0,0)

        # Wait for the result
        if inference_network.wait(cur_request_id) == 0:
            det_time = time.time() - inf_start

            # Get the results of the inference request 
            result = inference_network.get_output(cur_request_id)
            
            # Draw Bounting Box
            frame, current_count, d, tk = make_outputs(result, frame, in_w, in_h, temp, tk)
            
            # Printing Inference Time 
            inf_time_message = "Inference time: {:.3f}ms".format(det_time * 1000)
            cv2.putText(frame, inf_time_message, (15, 15), cv2.FONT_HERSHEY_COMPLEX, 0.5, color, 1)
            
            # Calculate and send relevant information 
            if current_count > last_count: # New entry
                start_time = time.time()
                total_count = total_count + current_count - last_count
                client.publish("person", json.dumps({"total": total_count}))            
            
            if current_count < last_count: # Average Time
                duration = int(time.time() - start_time) 
                client.publish("person/duration", json.dumps({"duration": duration}))
           
            # Adding overlays to the frame            
            txt2 = "Distance: %d" %d + " Lost frame: %d" %tk
            cv2.putText(frame, txt2, (15, 30), cv2.FONT_HERSHEY_COMPLEX, 0.5, color, 1)
            
            txt2 = "Current count: %d " %current_count
            cv2.putText(frame, txt2, (15, 45), cv2.FONT_HERSHEY_COMPLEX, 0.5, color, 1)

            if current_count > 3:
                txt2 = "Alert! Maximum count reached"
                (text_width, text_height) = cv2.getTextSize(txt2, cv2.FONT_HERSHEY_COMPLEX, 0.5, thickness=1)[0]
                text_offset_x = 10
                text_offset_y = frame.shape[0] - 10
                # coords of the box with a small padding of two pixels
                box_coords = ((text_offset_x, text_offset_y + 2), (text_offset_x + text_width, text_offset_y - text_height - 2))
                cv2.rectangle(frame, box_coords[0], box_coords[1], (0, 0, 0), cv2.FILLED)
                
                cv2.putText(frame, txt2, (text_offset_x, text_offset_y), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1)
            
            client.publish("person", json.dumps({"count": current_count}))

            last_count = current_count
            temp = d

            if key_pressed == 27:
                break

        # Send the frame to the FFMPEG server
        sys.stdout.buffer.write(frame)  
        sys.stdout.flush()
        if single_img:
            cv2.imwrite('output.jpg', frame)
       
    cap.release()
    cv2.destroyAllWindows()
    client.disconnect()
    inference_network.clean()
    
def main():
    args = build_argparser().parse_args()
    client = connect_mqtt()
    # Perform inference on the input-stream
    infer_on_stream(args, client)


if __name__ == '__main__':
    main()
