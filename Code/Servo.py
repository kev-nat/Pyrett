import numpy as np
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as sub
import time
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import AngularServo
from time import sleep

factory = PiGPIOFactory()

left_r = AngularServo(25, min_pulse_width=0.0006, max_pulse_width=0.0023, min_angle=-90, max_angle=90, pin_factory=factory)
angle_lr=45
left_r.angle = angle_lr

up_d = AngularServo(8, min_pulse_width=0.0006, max_pulse_width=0.0023, min_angle=-90, max_angle=90, pin_factory=factory)
angle_ud=45
up_d.angle = angle_ud
wake=""
state = "no"
e_x, e_y=0 , 60

# A callback function
def on_message_coord(client, userdata, msg):
    global e_x,e_y
    coords = msg.payload.decode('utf-8')
    coords = str(coords)
    coord = coords.split(',')
    # print(len(state))
    if len(state)>2:
        e_x= float(coord[0])
        e_y=float(coord[1])

def on_message_fire_state(client, userdata, msg):
    global state
    state=msg.payload.decode('utf-8')
    # print(state)

def on_message_wake(client, userdata, msg):
    
    # print (state)
    # print("sweeping")
    # print('done')
    global wake
    wake=msg.payload.decode('utf-8')

client = mqtt.Client()
client.message_callback_add('pyrett/turret', on_message_coord)
client.message_callback_add('pyrett/fire_state', on_message_fire_state)
client.message_callback_add('pyrett/wake', on_message_wake)
client.connect('192.168.1.6', 1883)

# Start a new thread
client.loop_start()
client.subscribe("pyrett/#")

timer = 0
active=False

while True:
    if wake:
        print('wake')
        angle_lr=45
        while not len(state)>2:
            msg = sub.simple("pyrett/fire_state", hostname="192.168.1.6")
            fs = msg.payload.decode('utf-8')
            angle_lr += -1
            
            if angle_lr < -90:
                angle_lr = -89
            left_r.angle = angle_lr
            
            if len(fs)>2:
                print("break")
                active = True
                break
            
            else:
                timer +=0.05
                print(timer)
                
                if timer > 10:
                    left_r.angle =45
                    up_d.angle =45
                    timer = 0
                    active = False
                    break
                
    if not len(state)>2:
        e_x= 0
        e_y= 60
        
        if active:
            timer +=0.05
            print(timer)
            
            if timer > 7:
                left_r.angle =45
                up_d.angle =45
                timer = 0
                active = False
                
    else:
        timer=0

    sleep(0.05)
    
    if active:
        if not len(state)>2:
            e_x, e_y=0 , 75

        if e_x < -40:
            angle_lr += -1
            if angle_lr < -90:
                angle_lr = -90
            left_r.angle = angle_lr
            
        elif e_x > 40:
            angle_lr += 1
            if angle_lr > 90:
                angle_lr = 90
            left_r.angle = angle_lr

        if e_y < 50:
            angle_ud += -1
            if angle_ud < -90:
                angle_ud = -89
            up_d.angle = angle_ud
            
        elif e_y > 100:
            angle_ud += 1
            if angle_ud > 90:
                angle_ud = 89
            up_d.angle = angle_ud
    else:
        pass
    
    # print(angle_ud, angle_lr,e_x,e_y)