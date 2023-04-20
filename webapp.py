import argparse
import torch
import numpy as np
import tensorflow as tf
from re import DEBUG, sub
from flask import Flask, render_template, request, redirect, send_file, url_for, Response
from werkzeug.utils import secure_filename, send_from_directory
import os
from subprocess import Popen
import paho.mqtt.client as paho
from paho.mqtt import client as mqtt_client
import requests
from flask import render_template_string
from selenium.webdriver.support import expected_conditions as EC
import cv2
import shutil
app = Flask(__name__)
image_changed = False
error_mapping = {
    '0': 'Spaghetti: ',
    '1': 'Stringging: -Try increasing the retraction distance by 1mm\n-Try adjust the retraction speed to 1200-6000 mm/min (20-100 mm/s)\n-Try decreasing your extruder temperature by 5-10 degrees\n-Be aware that in long movements stringing is more likely to happen.',
    '2': 'under extrusion: ',
    '3': 'warping: ',
    '4': 'zits: ',
    '5': 'There are no defects in this image. Try to decrease the threshold value.'
}

client= paho.Client()
broker="mqtt.beebotte.com"
port = 1883
topic = "tese_Andre/send_foto"
client_id = 'token_M4B4F8L2qr251vIR'
client.username_pw_set('token_M4B4F8L2qr251vIR')

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Successfully connected to MQTT broker")
        else:
            print("Failed to connect, return code %d", rc)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client
    
def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        f = open('C://Users//Public//received.jpg', 'wb')
        f.write(msg.payload)
        f.close()
        print ('image received')
        url = "http://localhost:5000"
        files = {'file': ('image.jpg', open('C://Users//Public//2fiutpt5uva41eeeg.jpg', 'rb'), 'image/jpg')}
        response=requests.post(url, files=files)
    client.subscribe(topic)
    client.on_message = on_message

@app.route('/save', methods=["POST"])
def save_photo():
    global filename
    request.form["imagePath"]
    imagePath = image_path
    folder_path = 'runs/detect'
    subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]    
    latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))    
    directory = folder_path + '/' + latest_subfolder + '/' +  os.path.splitext(filename)[0] + '.txt'
    
    with open(imagePath, 'rb') as f:
        file_data = f.read()
    filename = os.path.basename(imagePath)
    destination_path = os.path.join('C://Users//ferre//OneDrive//Ambiente de Trabalho//tese//tese_interface_git//dataset//train//images', filename)
    shutil.copy(directory, 'C://Users//ferre//OneDrive//Ambiente de Trabalho//tese//tese_interface_git//dataset//train//labels')
    
    with open(destination_path, 'wb') as f:
        f.write(file_data)
    return "OK"

@app.route('/takePhoto', methods=["POST"])
def take_photo():
    cam = cv2.VideoCapture('http://192.168.137.199:4747/video?640x480')
    result, image = cam.read()
    cam.release()
    if result:
        cv2.imwrite("C://Users//Public//received.jpg", image)
        url = "http://localhost:5000"
        files = {'file': ('image.jpg', open('C://Users//Public//received1.jpg', 'rb'), 'image/jpg')}
        response = requests.post(url, files=files)
        return "OK"
    else:
        raise ValueError("Failed to capture frame from video stream")

#The display function is used to serve the image or video from the folder_path directory.
@app.route('/<path:filename>')
def display(filename):
    folder_path = 'runs/detect'
    subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]    
    latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))    
    directory = folder_path + '/' +latest_subfolder
    #print("printing directory: ",directory)  
    filename = predict_img.imgpath
    print("file: "+filename)
    file_extension = filename.rsplit('.', 1)[1].lower()

    environ = request.environ
    if file_extension == 'jpg':      
        return send_from_directory(directory,filename,environ)

    elif file_extension == 'mp4':
        return render_template('index.html')

    else:
        return "Invalid file format"

@app.route("/sliderValue", methods=["POST"])
def handle_slider_update():
    global slider_value
    slider_value = request.form["sliderValue"]
    slider_value = int(slider_value)
    print("Tresh com valor0: ", slider_value)
    #print("Slider value:", slider_value)
    return "OK"

@app.route("/image_change", methods=["GET"])
def get_img_change():
    global image_changed
    if image_changed == True:
        image_changed = False 
        return {'image_changed': True}    
    else: 
        return {'image_changed': False} 

@app.route("/", methods=["GET", "POST"])
def predict_img():
    global image_path
    global error_list_message
    global image_changed
    global filename
    global slider_value
    if request.method == "POST":
        if 'file' in request.files:   
            f = request.files['file']
            basepath = os.path.dirname(__file__)
            #print("printing Basepath: ",basepath)
            if f.filename == '':
                filepath = os.path.join(basepath,'uploads',filename)
                file_extension = filename.rsplit('.', 1)[1].lower() 
                predict_img.imgpath = filename
            else:
                filepath = os.path.join(basepath,'uploads',f.filename)
                filename = f.filename
                predict_img.imgpath = f.filename
                f.save(filepath)
                file_extension = f.filename.rsplit('.', 1)[1].lower() 
                print(filename)
            #print("upload folder is ", filepath)
            print("Predicting Image =====>  ", predict_img)

            if 'submit' in request.form:
                #print("entrei 0")
                slider_value = request.form['slider']
                tresh = int(slider_value)/100 
                slider_value = int(slider_value)
                print("Tresh com valor1: ", tresh)
            else:
                tresh = int(slider_value)/100 
                print("Tresh com valor2: ", tresh)
        
            if file_extension == 'jpg':
                print("Tresh com valor3: ", tresh)
                process = Popen(["python", "detect1.py", '--source', filepath, "--weights", "best.pt", "--conf-thres",str(tresh)], shell=True)
                process.wait()
                
            elif file_extension == 'mp4':
                process = Popen(["python", "detect1.py", '--source', filepath, "--weights", "best.pt", "--conf-thres",str(tresh)], shell=True)
                process.communicate()
                process.wait()
                
        folder_path = 'runs/detect'
        subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]    
        latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))    
        if f.filename == '': 
            image_path = folder_path + '/' + latest_subfolder + '/'+ filename 
            print("image path: " + str(image_path))
        else:
            image_path = folder_path + '/' + latest_subfolder + '/'+ f.filename
            print("image path: " + str(image_path))

        txt_file = image_path.split('.')[0] + '.txt'
        if os.path.isfile(txt_file):
            with open(txt_file, 'r') as file:
                error_list = []
                for line in file:
                    error_type = line.split(' ')[0]
                    if error_type not in error_list:
                        error_list.append(error_type)
                # Print the list of first elements
                #print(error_list)
                error_list_message = [error_mapping[error] for error in error_list]
                print(error_list_message)
        else:
            error_list = ['5']
            error_list_message = [error_mapping[error] for error in error_list]
        #print(image_path)
        if 'submit' not in request.form:
            image_changed = True
    try:
        tresh = slider_value/100
        #slider_value=50
        print("Tresh com valor4: ", tresh)
        return render_template('index.html', image_path = image_path, variavel = error_list_message, thresh = tresh*100)
    except:
        return render_template('index.html')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask app exposing yolov7 models")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    args = parser.parse_args()
    model = torch.hub.load('.', 'custom','best.pt', source='local')
    client = connect_mqtt()
    subscribe(client)
    model.eval()
    client.loop_start()
    app.run(host="0.0.0.0", port=args.port)  # debug=True causes Restarting with stat