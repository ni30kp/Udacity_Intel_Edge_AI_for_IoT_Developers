# Project Write-Up

Goals for this project:
* Deploy the people counter app on the nVidia Jetson TX1 platform with use of Intel Neural Compute Stick 2.
* Integrate people counter app with real camera.

*__Note__: nVidia Jetson TX1 platform is just an example of edge device that can be used together with Intel Neural Compute Stick 2. Although Rasberry Pi would be cheaper alternative it is still more a device for consumer electronics market rather then for real industrial deployment.*

Identified features list:
* Use Aedes MQTT server instead of Mosca MQTT server (Mosca MQTT server is outdated and cannot be compiled on ARM64 architecture),
* Enable auto-refresh of video within the UI in case video stream is interrupted (currently video refresh is only performed once video is clicked),
* Select the model that will be incorporated into the app,
* Integrate camera feed.

## Explaining Custom Layers

The process behind converting custom layers involves, depending on original model framework:
* Both Caffe & TensorFlow: Register as extensions,
* Caffe-only: Use Caffe to calculate output shape,
* TensorFlow-only: Replace subgraph with another,
* TensorFlow-only: Offload computation to TensorFlow.

Some of the potential reasons for handling custom layers are:
* unsupported layers cannot be executed on the target accelerator and are automatically classified by model optimizer as custom layers,
* there is a need to add customized pre- and post- processing layers.

## Comparing Model Performance

My method(s) to compare models before and after conversion to Intermediate Representations were following:
* I used original model to infer on CPU using original framework then,
* I used converted model to infer on CPU using OpenVINO Toolkit so that,
* I was able to compare accuracy and speed of the inference.

The difference between model accuracy pre- and post-conversion was almost not noticeable.

The size of the converted model was roughly more then twice smaller then converted model mostly due to the fact that conversion was made from FP32 representation to FP16 representation. 

The inference time of the converted model was shorter when comparing it to the original model.

## Assess Model Use Cases

Some of the potential use cases of the people counter app or the app developed with the same or similar principles are:
* Estimation of vehicle traffic on the road combined with traffic light system,
* Estimation of wildlife population to enable appropriately balance the species of animals,
* Automatic feeding system,
* Passenger counter in public transportation.

Each of these use cases would be useful because:
* they give additional statistical information about particular scenario,
* enable to trigger defined action in certain conditions to actively react on detected situation.

## Assess Effects on End User Needs

Lighting, model accuracy, and camera focal length/image size have different effects on a
deployed edge model. The potential effects of each of these are as follows:
* increased/decreased number of false positives,
* increased/decreased number of false negatives,
* increased/decreased error in statistical measurements,
* better/worse reaction on the detected situation,
* faster/slower reaction time on the detected situation.

## Model Research

In investigating potential people counter models, I tried each of the following three models:

- Model 1: __faster_rcnn_inceetion_v2_coco__
  - Open Model Zoo
  - I converted the model to an Intermediate Representation with the following [script](model/faster_rcnn_inception_v2_coco.sh).
  - The model was sufficient for the app because it was very accurate.
  - I tried to deploy the model on the nVidia Jetson TX1 device with use of Intel Neural Compute Stick 2 and I figured out that the model is too heavy for the target edge device deployment (original model requires ~30.7 GFlops).
  - I decided to use that model as ground truth system for the statistical information.
  
- Model 2: __ssd_mobilenet_v2_coco__
  - Open Model Zoo.
  - I converted the model to an Intermediate Representation with the following [script](model/ssd_mobilenet_v2_coco.sh).
  - The model was insufficient for the app because its accuracy was limited. The model was not able to detect person on every frame which lead to incorrect statistical information.
  - I tried to improve the model for the app by applying number of filters on post processed signals. I managed to obtain identical results as for Model 1. The original model requires only ~3.8 GFlops and converted fits the target edge device deployment.

- Model 3: __ssdlite_mobilenet_v2__
  - Open Model Zoo
  - I converted the model to an Intermediate Representation with the following [script](model/ssdlite_mobilenet_v2.sh).
  - The model was similar to Model 2 and returned the same results but was more then twice better optimized (1.5 GFlops for original model) and potentially required less compute power.
  - Better optimized model potentially enables to used cheaper device such as Intel Movidius Neural Compute Stick.

- TODO: Model 4: __deeplabv3__
  - Open Model Zoo
  - I also considered this model for the target edge device deployment.
  - Based on the model description it may be more accurate then Model 2 and Model 3 and still fit into the the target edge device deployment.
  - The model had completely different architecture and input/output layers then Model 1, Model 2, Model 3 and it would require to redesign the people counter app. I decided to postpone its use for the next version of the app.