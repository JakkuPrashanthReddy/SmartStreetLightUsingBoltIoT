import json
import time
from datetime import datetime
from csv import writer
import requests
from boltiot import Bolt

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


print("Smart Street Light Monitoring Has Started...")

bolt = Bolt(configuration.bolt_api_key, configuration.device_id)

flag = 0     # to check Whether the Lights were Turned on or Turned off

LIST = []    # To store Sensor value and Time stamp

try:
    while True:
        response = bolt.analogRead('A0')
        data = json.loads(response)

        if data['value'] == 'Device is offline':
            print(data['value'])
            print("\nPlease turn on Your Device...")
            time.sleep(10)
            continue
        
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
        store_data(LIST)
        LIST.clear()
        time.sleep(10)
except Exception as e:
    print("\nThis is the Error caused : ", e)
