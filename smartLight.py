import json
import time
from datetime import datetime
from csv import writer
import requests
from boltiot import Bolt
import pandas as pd
import math
import statistics
import configuration


def send_telegram_message(message_):
    url = "https://api.telegram.org/" + configuration.bot_id + "/sendMessage"
    data_ = {
        "chat_id": configuration.chat_id,
        "text": message_
    }
    try:
        response_ = requests.request("POST", url, params=data_)
        telegram_data = json.loads(response_.text)
        return telegram_data["ok"]
    except Exception as exception:
        print("\nThere is an Error in sending Telegram Message....")
        print("This is the Error : ", exception)


def get_date_time():
    now = datetime.now()
    current_time_ = now.strftime("Date : %B %d, %Y \n Time : %H:%M:%S")
    return current_time_


def get_time_stamp():
    now = datetime.now()
    time_stamp = now.strftime("%d/%m/%y %H:%M:%S")
    return time_stamp


def store_data(List):
    with open('LightData.csv', 'a') as f:
        Writer = writer(f)
        Writer.writerow(List)
        f.close()
        print("Data Stored Successfully...")

def compute_bounds(frame_list):
    if len(frame_list) < configuration.frame_size:
        return None
    if len(frame_list) > configuration.frame_size:
        del frame_list[0 : len(frame_list) - configuration.frame_size]

    Variance = statistics.variance(frame_list)
    print("Variance : ",Variance)
    Zn = configuration.Multiplication_factor * math.sqrt(Variance/len(frame_list))
    print("z-score : ",Zn)
    Higher_Bound = frame_list[-1] + Zn
    Lower_Bound = frame_list[-1] - Zn
    return [Higher_Bound,Lower_Bound]

def anomaly(sensor_value):
    col_list = ['Timestamp','SensorValue','flag','HigherBound','LowerBound']
    df = pd.read_csv('LightData.csv', usecols=col_list)
    f_list = df['SensorValue']
    frame_list = [x for x in f_list if math.isnan(x) == False]

    bound = compute_bounds(frame_list)
    print("This are boundaries :",bound)
    if not bound:
        required_data_count=configuration.frame_size - len(frame_list)
        print("Not enough data to compute Z-score. Need ",required_data_count," more data points")
        frame_list.append(int(data['value']))
        time.sleep(10)
        return [0,0]

    time_ = get_date_time()
    if sensor_value > bound[0] and sensor_value > configuration.maximum:
        print("sensor value crossed boundary",bound[0])
        message = "Something went Worng with Street lights......\n Street lights turned off At wrong time \n "+ time_
        print(message)
        print("\nRequesting Telegram to send Message...")
        return_response = send_telegram_message(message)
        print("Response from Telegram : ", return_response)
        time.sleep(10)

    if  sensor_value < bound[1] and sensor_value < configuration.minimum:
        print("sensor value crossed boundary",bound[1])
        message = "Something went Worng with Street lights......\n Street lights turned on At wrong time \n "+ time_
        print(message)
        print("\nRequesting Telegram to send Message...")
        return_response = send_telegram_message(message)
        print("Response from Telegram : ", return_response)
        time.sleep(10)

    return bound      

def get_flag_value():
    col_list = ['Timestamp','SensorValue','flag','HigherBound','LowerBound']
    df = pd.read_csv('LightData.csv', usecols=col_list)
    f_list = df['flag']
    frame_list = [x for x in f_list if math.isnan(x) == False]
    return frame_list[-1]

print("Smart Street Light Monitoring Has Started...")

bolt = Bolt(configuration.bolt_api_key, configuration.device_id)
flag = get_flag_value()
flag1 =0
LIST = []

try:
    while True:
        response = bolt.analogRead('A0')
        data = json.loads(response)
        if data['value'] == 'Device is offline':
            print("\n"+data['value'])
            print("Please turn on Your Device...")
            if flag1 != 1:
                message = "Your Light Monitoring device is offline \n Please Turn it ON"
                print("\nRequesting Telegram to send Message...")
                return_response = send_telegram_message(message)
                print("Response from Telegram : ", return_response)
                flag1 = 1

            time.sleep(10)
            continue

        flag1 = 0
        sensor_value = int(data['value'])

        LIST.append(get_time_stamp())
        LIST.append(sensor_value)

        print("\nThis is the Sensor Value : ", sensor_value)
        if sensor_value <= configuration.minimum:
            if flag != 1:
                response = bolt.digitalWrite(configuration.PIN, 'HIGH')
                current_time = get_date_time()
                message = "Street Lights Turned ON \n " + str(current_time) + "\n- With ❤ Smart Street Light "
                data = json.loads(response)
                if int(data['success']) == 1:
                    print("\nRequesting Telegram to send Message...")
                    return_response = send_telegram_message(message)
                    print("Response from Telegram : ", return_response)
            flag = 1
        if sensor_value >= configuration.maximum:
            if flag != 0:
                response = bolt.digitalWrite(configuration.PIN, 'LOW')
                current_time = get_date_time()
                message = "Street Lights Turned OFF \n " + str(current_time) + "\n- With ❤ Smart Street Light "
                data = json.loads(response)
                if int(data['success']) == 1:
                    print("\nRequesting Telegram to send Message...")
                    return_response = send_telegram_message(message)
                    print("Response from Telegram : ", return_response)
            flag = 0
        anomalydata = anomaly(sensor_value)
        LIST.append(flag)
        LIST.append(anomalydata[0])
        LIST.append(anomalydata[1])
        store_data(LIST)
        LIST.clear()
        time.sleep(10)
except Exception as e:
    print("\nThis is the Error caused : ", e)
