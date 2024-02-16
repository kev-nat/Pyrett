import paho.mqtt.subscribe as sub
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
pin=14
GPIO.setup(pin,GPIO.OUT)
GPIO.output(pin,False)

def on_message_wake(client, userdata, msg):
    global wake
    wake=msg.payload.decode('utf-8')

client = mqtt.Client()
client.message_callback_add('pyrett/wake', on_message_wake)
client.connect('192.168.1.6', 1883)
client.loop_start()
client.subscribe("pyrett/#")
wake=''
timer = 1
GPIO.output(pin,True)
while True:
    if wake:
        
        while True:
            print("wake")
            msg = sub.simple("pyrett/fire_state", hostname="192.168.1.6")
            state=msg.payload.decode('utf-8')
            if len(state)>2:
                time.sleep(2)
                print(state)
                GPIO.output(pin,False)
                timer = 0
            else:
                GPIO.output(pin,True)
                time.sleep(1)
                timer += 1
                print (timer)
                if timer >20:
                    print('break')
                    timer = 0
                    break
                
        