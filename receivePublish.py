#!/usr/bin/env python
import pika
import time
import configparser
import uuid
import json
import os
import subprocess



config = configparser.ConfigParser()
config.read('config.ini')

credentials = pika.PlainCredentials(config['DEFAULT']['USERNAME'], config['DEFAULT']['PASSWORD'])
hostName = config['DEFAULT']['HOST_NAME']
portNumber = config['DEFAULT']['PORT']
virtualHost = config['DEFAULT']['VIRTUAL_HOST']

lrInstallPath = config['DEFAULT']['VUGEN_INSTALL_PATH']
scriptPath = config['DEFAULT']['VUGEN_SCRIPT_PATH']
scriptName = config['DEFAULT']['VUGEN_SCRIPT_NAME']
responseQueueName =  config['DEFAULT']['QUEUE_NAME_RESPONSE']
requestQueueName =  config['DEFAULT']['QUEUE_NAME_REQUEST']


parameters = pika.ConnectionParameters(
    host=hostName,
    port='5672',#'5672',
    virtual_host='test',
    credentials=credentials)

####
#   Method to parse message
#   {"uuid": UUID, "Request": { "api-name": "pstnCheck","no": no }}
####
def parseMessage(body):
    
    json_string = '{ "uuid":"1231","Request":{"api-name":"Check","fnn":"0303030303" } }'
    
    data = json.loads(json_string)
   
   # 1. Parse JSON to retrieve fnn and uuid
    paramFnn = data['Request']['fnn']
    requestUUID = data['uuid']

    # 2. Generate the command to be executed
    command = lrInstallPath + " " + scriptPath + scriptName + "\\" + scriptName + ".usr" + " -fnn "  + paramFnn + " -uuid "  + requestUUID +  " -out D:\\tmp\\output"
    print("Command: " + command)

    # 3. Execute the command
    p = subprocess.Popen(command,  stdout=subprocess.PIPE, shell=True)

    (output, err) = p.communicate()  

    # 4. This makes the wait possible
    p_status = p.wait()

    # 5. Read the result from json file
    outputFile = "D:/tmp/"+requestUUID+"_"+paramFnn+".txt"
    print ("OutputFile" + outputFile)
    file = open(outputFile,"r")
    outputJson = file.read().replace('\\','')

    #cleanJson = ouptutJson.replace('\\','')
#    re.sub

    # 6. Build response json
    print ("OutputJson " + outputJson)
    data['Response']=outputJson
    print(json.dumps(data))

    # 7. Send message to publisher
    sendMessage(json.dumps(data))
    
    
# Send Message to response queue
def sendMessage(data):
    sendConnection = pika.BlockingConnection(parameters)
    sendChannel = sendConnection.channel()
    sendChannel.queue_declare(queue=responseQueueName, durable=False)
    sendChannel.basic_publish(exchange='',
                      routing_key=responseQueueName,
                      body=data
                      )
    print("Message Sent")
    
    sendConnection.close()
    

parseMessage("Test")

# Create connection and consume
connection = pika.BlockingConnection(parameters)

channel = connection.channel()

consumeQueue = config['DEFAULT']['QUEUE_NAME_REQUEST']
#sendResponseQueue = config['DEFAULT']['QUEUE_NAME_RESPONSE']
channel.queue_declare(queue=consumeQueue, durable=False)
print(' [*] Waiting for messages. To exit press CTRL+C')

#####
#   Method to consume message
#####
def callback(ch, method, properties, body):
    
    
    ch.basic_ack(delivery_tag = method.delivery_tag)
    print(" [x] Received %r" % body)
    #time.sleep(body.count(b'.'))
    #parseMessage(body)
    print(" [x] Done")
    ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue=consumeQueue)


channel.start_consuming()

