import numpy as np
import cv2
import paho.mqtt.client as mqtt
import random
import time
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator

model = YOLO('best.pt')
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_EXPOSURE,-6)

mqttClient = mqtt.Client()
mqttClient.connect('localhost', 1883)
mqttClient.loop_start()

# Define source points (in the order top-left, top-right, bottom-right, bottom-left)
src_pts = np.float32([[139, 10],[1149, 10],[3, 699],[1252, 713]])

# Define corresponding destination points
dst_pts = np.float32([[0,0],[1280,0],[0,820],[1280,820]])

perspective_matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

while True:
    _, img = cap.read()
    
    transformed_frame = cv2.warpPerspective(img, perspective_matrix, (1280,820))
    
    results = model.predict(transformed_frame,stream=True,conf = 0.20)

    for r in results:
        
        annotator = Annotator(transformed_frame)
        
        boxes = r.boxes.numpy()
        for box in boxes:
            
            b = box.xyxy[0]  # get box coordinates in (top, left, bottom, right) format
            c = box.xywh[0]
            x=c[0]
            y=c[1]
            
            coord = str(x) + ' , '+str(y)
            annotator.box_label(b, coord)
            
            info = mqttClient.publish(
                topic='pyrett/YOLO_coord',
                payload=coord.encode('utf-8'),
                qos=0,
            )
            info.wait_for_publish()
            
    img = annotator.result()  
    cv2.imshow('YOLO V8 Detection', img)     
    if cv2.waitKey(1) & 0xFF == ord(' '):
        break

cap.release()
cv2.destroyAllWindows()