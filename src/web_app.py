from flask import Flask, request, render_template
from sendEmail import send_email
from weather import get_timestamp
from sense_hat import SenseHat
import os
import csv
import ast
import tablib
import pandas as pd


app = Flask(__name__)

dataset = tablib.Dataset()



def get_csv_data():
    """Open the daily csv log and return the content"""
    csv_list = []
    day = get_timestamp().split()[0]
    csv_path = os.path.join(os.path.dirname(__file__) + '/logs/', day + '.csv')
    # csv_path = '/home/pi/Pi_Weather_Station/src/logs/' + day + '.csv'
    with open(csv_path, 'r') as csv_file:
        # content = f.read()
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            # print(row)
            csv_list.append(row)
    return csv_list

# print(get_csv_data())

def get_dark_sky():
    """Read the most recent dark sky log and return a list of the stats"""
    csv_content = get_csv_data()
    most_recent = csv_content[-1]
    dark_sky_string = most_recent[9]
    dark_sky_list = dark_sky_string.strip('][').split(', ')
    ds_temp = dark_sky_list[0]
    ds_cond = dark_sky_list[1].strip("'")
    ds_fore = dark_sky_list[2].strip("'")
    return [ds_temp, ds_cond, ds_fore]

# print(get_dark_sky())

def get_gov_aqi():
    """Read the most recent aqi log and return the stats"""
    csv_content = get_csv_data()
    most_recent = csv_content[-1]
    aqi_string = most_recent[10]
    aqi_list = aqi_string.strip('][').split(', ')
    aqi = aqi_list[0]
    air_cond = aqi_list[1].strip("'")
    return [aqi, air_cond]

# print(get_gov_aqi())


def save_alert(result_dict):
    """Take a list and save it as a csv"""
    # src_dir = os.path.dirname(os.path.realpath(__file__))
    # w_log = os.path.join(src_dir + '/logs/', day + '.csv')
    file_path = '/home/pi/Pi_Weather_Station/src/alerts.txt'
    with open(file_path, 'w') as output:
        output.write(str(result_dict))


def read_alert():
    file_path = '/home/pi/Pi_Weather_Station/src/alerts.txt'
    with open(file_path, 'r') as input:
        s = input.read()
        whip = ast.literal_eval(s)
    return whip


def update_logs_html():        
    day = get_timestamp().split()[0]
    csv_path = '/home/pi/Pi_Weather_Station/src/logs/' + day + '.csv'
    columns = ['Log Time', 'Temp (C)', 'Temp (F)', 'Humidity', 'Pressure', 'DewPoint', 'X', 'Y', 'Z', 'Weather', 'AQI']
    df = pd.read_csv(csv_path, names=columns)
    with open('/home/pi/Pi_Weather_Station/src/templates/logs.html', 'w') as html_file:
        html_file.write(df.to_html())


@app.route('/')
def index():
    sense = SenseHat()
    sense.clear()

    acceleration = sense.get_accelerometer_raw()
    celsius      = round(sense.get_temperature(), 1)
    kwargs = dict(
        celsius     = celsius,
        fahrenheit  = round(1.8 * celsius + 32, 1),
        humidity    = round(sense.get_humidity(), 1),
        pressure    = round(sense.get_pressure(), 1),
        x = round(acceleration['x'], 2),
        y = round(acceleration['y'], 2),
        z = round(acceleration['z'], 2),
    )
    aqi = get_gov_aqi()
    dark_sky = get_dark_sky()
    return render_template('weather.html', **kwargs, aqi=aqi, dark_sky=dark_sky)


@app.route('/old')
def old():
    sense = SenseHat()
    sense.clear()

    acceleration = sense.get_accelerometer_raw()
    celsius      = round(sense.get_temperature(), 1)
    kwargs = dict(
        celsius     = celsius,
        fahrenheit  = round(1.8 * celsius + 32, 1),
        humidity    = round(sense.get_humidity(), 1),
        pressure    = round(sense.get_pressure(), 1),
        x = round(acceleration['x'], 2),
        y = round(acceleration['y'], 2),
        z = round(acceleration['z'], 2),
    )
    aqi = get_gov_aqi()
    dark_sky = get_dark_sky()
    return render_template('weather_old.html', **kwargs, aqi=aqi, dark_sky=dark_sky)


@app.route('/alerts/', methods=['POST', 'GET'])
def alerts():
    if request.method == 'POST':
        min_temp = request.form['mintemp']
        max_temp = request.form['maxtemp']
        aqi_max = request.form['aqimax']
        alert_dict = {}
        alert_dict['min_temp'] = min_temp
        alert_dict['max_temp'] = max_temp
        alert_dict['aqi_max'] = aqi_max
        save_alert(alert_dict)
        stat_dict = read_alert()
        return render_template('alerts.html', stat_dict=stat_dict)
    else:
        stat_dict = read_alert()
        return render_template('alerts.html', stat_dict=stat_dict)


@app.route('/logs/')
def logs_web():
    update_logs_html()
    return render_template('logs.html')


while __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
