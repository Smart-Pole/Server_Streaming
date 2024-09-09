import sys
import time
# from Adafruit_IO import MQTTClient
import paho.mqtt.client as MQTTClient

class MyMQTTClient:
    def __init__(self, username, token, topics, broker = "io.adafruit.com", port=1883 ):
        self.broker = broker   
        self.port = port
        self.username = username
        self.token = token
        self.topics = topics

        self.client = MQTTClient.Client()
        
            
        
        self.client.on_connect = self.connected
        self.client.on_disconnect = self.disconnected
        self.client.on_message = self.message
        self.client.on_subscribe = self.subscribe
        self.processMessage = None
        
        self.client.username_pw_set(self.username, self.token)
         

    def connected(self, client, userdata, flags, rc):
        print("Ket noi thanh cong ...")
        for topic in self.topics:
            self.client.subscribe(topic)

    def subscribe(self, client, userdata, mid, granted_qos):
        print("Subscribe thanh cong ...")

    def disconnected(self, client):
        print("Ngat ket noi ...")
        sys.exit(1)

    def message(self, client, userdata, message):
        topic_recv = message.topic
        payload_recv = message.payload.decode("UTF-8")
        print("Nhan du lieu: " + topic_recv + ":" + payload_recv)
        if self.processMessage != None:
            self.processMessage(message)

    def start(self):
        self.client.connect(host=self.broker,port=self.port)  
        self.client.loop_start() 

    def publish_data(self, topic,data):
        self.client.publish(topic, data)

if __name__ == "__main__":
    AIO_USERNAME = "NhanHuynh"
    AIO_KEY = ""
    AIO_FEED_ID = ["NhanHuynh/feeds/humi"]

    mqtt_client = MyMQTTClient(AIO_USERNAME, AIO_KEY, AIO_FEED_ID)
    
    while True:
        mqtt_client.publish_data("NhanHuynh/feeds/humi",100) 
        time.sleep(10)