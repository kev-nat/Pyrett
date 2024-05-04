import sys
import time
import RPi.GPIO as GPIO
import concurrent.futures
import numpy as np
import paho.mqtt.subscribe as sub
import time
import paho.mqtt.client as mqtt
import random
GPIO.setmode(GPIO.BCM)

dir_x,stp_x = 12,4      #dir x, step x

dir_y1,stp_y1 = 21,20   #dir y, step y

dir_y2,stp_y2 = 26,19   #dir y, step y

x_lmt1,x_lmt2 = 23,22   #x limit right ,left
y_lmt1,y_lmt2 = 13,6    #y limit right ,left
GPIO.setup([15,17,18], GPIO.OUT)
GPIO.setup([dir_x,stp_x,dir_y1,stp_y1,dir_y2,stp_y2], GPIO.OUT)
GPIO.setup([x_lmt1,x_lmt2,y_lmt1,y_lmt2], GPIO.IN)
GPIO.output(15,False)
GPIO.output(17,False)
GPIO.output(18,False)

def step(direction_pin,step_pin,clockwise):
    '''Function to step motor by 1'''
    GPIO.output(direction_pin, clockwise)
    stepdelay = 0.002
    GPIO.output(step_pin,True)
    time.sleep(stepdelay)
    GPIO.output(step_pin,False)
    time.sleep(stepdelay)

def step2(direction_pin,step_pin,clockwise):
    '''Function to step motor by 1'''
    GPIO.output(direction_pin, clockwise)
    stepdelay = 0.005
    GPIO.output(step_pin,True)
    time.sleep(stepdelay)
    GPIO.output(step_pin,False)
    time.sleep(stepdelay)
    
def new_step(steps,direction_pin,step_pin,clockwise,a,start_end_delay,max_v,switch):
    '''
        We are manipulating the delay between step() so longer delay will take more time to complete 
        a is percentage of steps to reach/exit max_v
        start_end_delay is the delay at the start and end of sequence of step
        max_v is the minimum delay in the sequence of steps
    '''
    global current_x, current_y

    steps_done=0
    m=(max_v-start_end_delay)/(((a/10)*steps)-1)
    b=max_v+m*((((10-a)/10)*steps)-1)
    while (steps_done < steps):
        step(direction_pin,step_pin,clockwise)
        
        if(not GPIO.input(switch)):
            if switch == 22 or switch == 23:
                current_x = 0
                
            elif switch == 6 or switch == 13:
                current_y = max_y
        
            break
        
        if (steps_done < ((a/10)*steps)):

            delay = (m*steps_done)+start_end_delay
            
        elif(steps_done < (((10-a)/10)*steps)):
            delay = max_v
            
        else:
            delay = (-m*steps_done)+b
        # print(delay, steps_done)
        steps_done+=1
        time.sleep(delay)
        
def new_step_cal(steps,direction_pin,step_pin,clockwise,a,start_end_delay,max_v,switch):
    '''
        We are manipulating the delay between step() so longer delay will take more time to complete 
        a is percentage of steps to reach/exit max_v
        start_end_delay is the delay at the start and end of sequence of step
        max_v is the minimum delay in the sequence of steps
    '''
    steps_done=0
    m=(max_v-start_end_delay)/(((a/10)*steps)-1)
    b=max_v+m*((((10-a)/10)*steps)-1)
    
    while (steps_done < steps):
        step(direction_pin,step_pin,clockwise)
        
        if (steps_done < ((a/10)*steps)):
            delay = (m*steps_done)+start_end_delay
            
        elif(steps_done < (((10-a)/10)*steps)):
            delay = max_v
            
        else:
            delay = (-m*steps_done)+b
            
        # print(delay, steps_done)
        steps_done+=1
        time.sleep(delay)

def cal_x():
    iterations = 0
    stepsx=0
    c=True
    steps_num_x = []
    
    while True:    
        step2(dir_x,stp_x,c)
        stepsx +=1
        
        # print(stepsx)
        right_button = not GPIO.input(x_lmt1)
        left_button =  not GPIO.input(22)
        # print(left_button)
        
        if left_button or right_button:
            time.sleep(2)
            iterations += 1
            
            if left_button:
                direction = "left"
                
            if right_button:
                direction = "right"
                
            # print(iterations,direction,stepsx)
            time.sleep(1)
            steps_num_x.append(stepsx)
            c= not c
            print('Button Pressed, return to init')
            
            new_step_cal(stepsx,dir_x,stp_x,c,1,0.01,0.005,22)
            stepsx = 0
            time.sleep(2)
            print('Button Pressed')
            
        if iterations == 2:
            print(['right','left'])
            print(steps_num_x)
            break
        
    max_x = steps_num_x[0] + steps_num_x[1]
    current_x = steps_num_x[1]
    return current_x, max_x

def cal_y():
    iterations = 0
    stepsy=0
    c=False
    steps_num_y = []
    
    while True:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            f1= executor.submit(step2,dir_y1,stp_y1,c)
            f2= executor.submit(step2,dir_y2,stp_y2,c)
        stepsy +=1
        # print(stepsx)
        
        up_button = not GPIO.input(y_lmt2)
        down_button = not GPIO.input(y_lmt1)
        # print(right_button)
        
        if down_button or up_button:
            time.sleep(2)
            iterations += 1
            if down_button:
                direction = "down"
                
            if up_button:
                direction = "up"
                
            # print(iterations,direction,stepsx)
            time.sleep(1)
            steps_num_y.append(stepsy)
            c= not c
            print('Button Pressed, return to init')
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                f1= executor.submit(new_step_cal,stepsy,dir_y1,stp_y1,c,1,0.01,0.005,6)
                f2= executor.submit(new_step_cal,stepsy,dir_y2,stp_y2,c,1,0.01,0.005,6)
            stepsy = 0
            time.sleep(2)
            # print('Button Pressed')
            
        if iterations == 2:
            print(['up','down'])
            print(steps_num_y)
            break
        
    max_y = steps_num_y[0] + steps_num_y[1]
    current_y = steps_num_y[1]
    return current_y, max_y

def call_all():
    current_y, max_y = cal_y()
    new_y = max_y*(80/100)
    steps_to_take_y = current_y - new_y
    
    if steps_to_take_y < 0:
        c_y = False
        steps_to_take_y = abs(steps_to_take_y)
        
    elif steps_to_take_y > 0:
        steps_to_take_y = abs(steps_to_take_y)
        c_y = True
        
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f1= executor.submit(new_step,steps_to_take_y,dir_y1,stp_y1,c_y,1,0.01,0.005,6)
        f2= executor.submit(new_step,steps_to_take_y,dir_y2,stp_y2,c_y,1,0.01,0.005,6)
    current_y = new_y

    current_x,max_x = cal_x()
    new_x = max_x*(5/100)
    steps_to_take_x = current_x - new_x
    
    if steps_to_take_x < 0:
        c_x = True
        steps_to_take_x = abs(steps_to_take_x)
        print('right')
        
    elif steps_to_take_x > 0:
        c_x = False
        steps_to_take_x = abs(steps_to_take_x)
        print('left')
        
    new_step(steps_to_take_x,dir_x,stp_x,c_x,1,0.01,0.005,22)
    current_x =new_x
    return current_x,current_y, max_x,max_y

def move_to(current_x,current_y,new_x,new_y, max_x,max_y):
    steps_to_take_x = current_x - new_x
    steps_to_take_y = current_y - new_y

    if new_x > max_x or new_x < 0:
        raise Exception("new x position is out of bounds")
    
    elif new_y > max_y or new_y < 0:
        raise Exception("new y position is out of bounds")
    
    # print(steps_to_take_x,steps_to_take_y)
    if steps_to_take_y < 0:
        c_y = False
        steps_to_take_y = abs(steps_to_take_y)
        
    elif steps_to_take_y > 0:
        steps_to_take_y = abs(steps_to_take_y)
        c_y = True

    if steps_to_take_x < 0:
        c_x = True
        steps_to_take_x = abs(steps_to_take_x)
        new_step(steps_to_take_x,dir_x,stp_x,c_x,1,0.01,0.005,22)
        print('right')
        
    elif steps_to_take_x > 0:
        c_x = False
        steps_to_take_x = abs(steps_to_take_x)
        new_step(steps_to_take_x,dir_x,stp_x,c_x,1,0.01,0.005,22)
        print('left')

    with concurrent.futures.ThreadPoolExecutor() as executor:
        f1= executor.submit(new_step,steps_to_take_y,dir_y1,stp_y1,c_y,1,0.01,0.005,6)
        f2= executor.submit(new_step,steps_to_take_y,dir_y2,stp_y2,c_y,1,0.01,0.005,6)

    current_y = new_y
    current_x =new_x
    return current_x, current_y

def coord_trans(x,y):
    tencm = (max_x/80.5)*20
    new_x= x - (tencm*np.cos(np.arctan(y/x)))
    new_y= y - (tencm*np.sin(np.arctan(y/x)))
    return new_x,new_y

# current_x, current_y, max_x, max_y = 734, 643, 1663, 1211
current_x, current_y, max_x, max_y = call_all()
new_x = max_x *(5/100)
new_y = max_y *(95/100)
current_x,current_y = move_to(current_x,current_y,new_x,new_y, max_x,max_y)
print(current_x, current_y, max_x, max_y)

# def on_message_fire_state(client, userdata, msg):
#     global state
#     state=msg.payload.decode('utf-8')

mqttClient = mqtt.Client()
mqttClient.connect('192.168.1.6', 1883)
# mqttClient.message_callback_add('pyrett/fire_state', on_message_fire_state)
mqttClient.loop_start()

time.sleep(0.5)
init = True
timer = 0
state='fire'

while True:
    if init == True:
        GPIO.output(15,False)
        GPIO.output(17,False)
        GPIO.output(18,False)
        #get coords
        msg = sub.simple("pyrett/YOLO_coord", hostname="192.168.1.6")
        coords = msg.payload.decode('utf-8')
        coords = str(coords)
        coord = coords.split(',')
        x= coord[0]
        y=coord[1]
        x , y =coord_trans(float(x) , float(y))
        x = np.interp(x,[0,1280],[0,max_x])
        y = np.interp(y,[0,820],[max_y,0])
        x=int(round(x,0))
        y=int(round(y,0))
        new_x = x
        new_y = y

        # Move to coordinates
        current_x,current_y = move_to(current_x,current_y,new_x,new_y, max_x,max_y)

        # Wake turret
        payload = 'wake'
        info = mqttClient.publish(
                    topic='pyrett/wake',
                    payload=payload.encode('utf-8'),
                    qos=0,
                )
        
        info.wait_for_publish()
        time.sleep(0.1)
        payload = ''
        info = mqttClient.publish(
                    topic='pyrett/wake',
                    payload=payload.encode('utf-8'),
                    qos=0,
                )
        info.wait_for_publish()
        print(current_x,current_y)
        init = False
        
    msg = sub.simple("pyrett/fire_state", hostname="192.168.1.6")
    fs = msg.payload.decode('utf-8')
    if len(fs) < 4:
        time.sleep(0.05)
        timer +=0.05
        print(timer)
        
        # Set enable to high to disable steppers
        if timer > 5:
            GPIO.output(15,False)
            GPIO.output(17,False)
            GPIO.output(18,False)
            new_x = max_x *(5/100)
            new_y = max_y *(95/100)
            current_x,current_y = move_to(current_x,current_y,new_x,new_y, max_x,max_y)
            timer = 0
            time.sleep(1)
            init = True
            
    else:
        timer = 0
        #set enable to low to enable steppers
        GPIO.output(15,True)
        GPIO.output(17,True)
        GPIO.output(18,True)