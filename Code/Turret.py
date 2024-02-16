from ultralytics import YOLO
import cv2
from ultralytics.utils.plotting import Annotator  # ultralytics.yolo.utils.plotting is deprecated
import numpy as np

import time
import paho.mqtt.client as mqtt
import random

model = YOLO('best.pt')
cap = cv2.VideoCapture(1)
cap.set(3, 1280/2)
cap.set(4, 720/2)
cap.set(cv2.CAP_PROP_EXPOSURE,-20)

mqttClient = mqtt.Client()
mqttClient.connect('localhost', 1883)
mqttClient.loop_start()

while True:
    _, img = cap.read()
    
    results = model.predict(img,verbose=False,stream=True,conf=0.3)
    
    for r in results:
        # print(len(r))
        annotator = Annotator(img)
        if len(r)<1:
            state = "no"
            info = mqttClient.publish(
            topic='pyrett/fire_state',
            payload=state.encode('utf-8'),
            qos=0,
            )
            info.wait_for_publish()

            coord = str(0) + ' , '+str(75)
            info = mqttClient.publish(
            topic='pyrett/turret',
            payload=coord.encode('utf-8'),
            qos=0,
            )
            info.wait_for_publish()
            print(coord)
        else:
            boxes = r.boxes.numpy()
            for box in boxes:
                
                b = box.xyxy[0]  # get box coordinates in (top, left, bottom, right) format
                c = box.xywh[0]
                x=c[0]
                y=c[1]
                x = np.interp(x,[0,640],[-320,320])
                y = np.interp(y,[0,320],[-160,160])
                coord = str(x) + ' , '+str(y)
                annotator.box_label(b, coord)
        
                info = mqttClient.publish(
                    topic='pyrett/turret',
                    payload=coord.encode('utf-8'),
                    qos=0,
                )
                info.wait_for_publish()
                state = "fire"
                info = mqttClient.publish(
                    topic='pyrett/fire_state',
                    payload=state.encode('utf-8'),
                    qos=0,
                )
                info.wait_for_publish()
                print(state)

    
    img = annotator.result()  
    cv2.imshow('YOLO V8 Detection', img)     
    if cv2.waitKey(1) & 0xFF == ord(' '):
        break

cap.release()
cv2.destroyAllWindows()