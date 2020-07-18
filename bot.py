# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

import json
import os
import re
from time import sleep
from dotenv import load_dotenv
import smtplib, ssl
from email.message import EmailMessage
from flask import Markup, flash
import symptom_analytics_ml.symptom_analytics as ml


import requests
from flask import Flask, render_template, request

load_dotenv('config/credentials.env')

# Retrieve required details from environment variables
bot_email = os.getenv('BOT_EMAIL')
teams_token = os.getenv('BOT_TOKEN')
bot_url = os.getenv('BOT_URL')
bot_app_name = os.getenv('BOT_NAME')
user_token = os.getenv('WEBEX_USER_TOKEN')
email_password = os.getenv('GMAIL_PASSWORD')

print(bot_email)

# Header information
headers = {
    'content-type': 'application/json; charset=utf-8',
    'authorization': 'Bearer ' + teams_token
}


def setup_bot_webhook():
    '''
    Setting up webhook
    '''
    url = "https://api.ciscospark.com/v1/webhooks"

    payload = {
      "name": "Patient Webhook",
      "resource": "all",
      "event": "all",
      "targetUrl": os.getenv('BOT_URL')
    }
    if_webhook_exists = check_webhook_id()
    if(if_webhook_exists == False):
        response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
        webhook_id = response.json()
        print(webhook_id['id'])
        if(response.status_code != 200):
            print("Webhook creation failed " +str(response.text))
        else:
            with open("webhook_id.txt", 'w') as filetowrite:
                filetowrite.write(webhook_id['id'])
            filetowrite.close()
            print("Webhook creation success "+str(response.text))
    else:
        print("Webhook exists for the URL specified "+str(os.getenv('BOT_URL')))

def check_webhook_id():
    '''
    Check if a webhook is already created for the Ngrok URL specified
    :return:
    '''
    f = open("webhook_id.txt", "r")
    id = f.read()  # Fetch guest token
    print("id - " + id)
    url = "https://api.ciscospark.com/v1/webhooks/"+id

    response = requests.request("GET", url, headers=headers)
    res = response.json()
    if(res['targetUrl'] == os.getenv('BOT_URL')):
        return True
    else:
        return False


def send_get(url, payload=None,js=True):
    '''
    Function to fetch message using Webex teams bot
    :param url: API endpoint URL
    :param payload: Data
    :param js: Boolean value
    :return: request
    '''

    if payload == None:
        request = requests.get(url, headers=headers)
    else:
        request = requests.get(url, headers=headers, params=payload)
    if js == True:
        request= request.json()
    return request


def send_post(url, data):
    '''
    Function to send message using Webex teams bot
    :param url: API endpoint URL
    :param data: Payload
    :return: request
    '''

    request = requests.post(url, json.dumps(data), headers=headers).json()
    return request


def help_me():
    '''
    Help message
    :return: message
    '''
    msg = "Sure! I can help. Below are the few things that I can help you with<br/>" \
           "- Book a virtual appointment with the nurse/doctor & send email notifications with webex meeting details.<br/>" \
           "- Emergency virtual assistance based on your symptoms and machine learning based analysis of your symptoms.<br>" \
           "- Securely transfer your lab test/vital reports to your doctor.<br>" \
           "- Secure QR code based digital prescription."

    return msg


def greetings():
    '''
    Welcome message
    :return: message
    '''
    return "Hi there, welcome to MediPlus!! My name is %s. please share your name, email address, location and patient ID.<br/>" % bot_app_name



def book_appointment(room, selected_option,patient_email):
    '''
    Book an appointment
    :param room: Webex roomId
    :return: None
    '''
    print(selected_option)
    if selected_option.__eq__("1"):
        slot = "02/Aug/2020 1pm"
        invite = schedule_meeting("2020-08-02T13:00:00-08:00","2020-08-02T14:00:00-08:00")
    elif selected_option.__eq__("2"):
        slot = "02/Aug/2020 3pm"
        invite = schedule_meeting("2020-08-02T15:00:00-08:00", "2020-08-02T16:00:00-08:00")
    elif selected_option.__eq__("3"):
        slot = "04/Aug/2020 11am"
        invite = schedule_meeting("2020-08-04T11:00:00-08:00", "2020-08-04T12:00:00-08:00")
    meeting_link = invite['webLink']
    meeting_password = invite['password']
    msg = "Appointment successfully booked for <b>"+slot+"</b>, kindly find the details of your virtual appointment with calendar information and Cisco Webex meeting link.<br/>" \
          "Booking ID: PA3214<br/>\n" \
          "Meeting Link: "+str(meeting_link)+" \n" \
          "\n Appointment details via Webex meetings is sent to your email id "+str(patient_email)
    send_post("https://api.ciscospark.com/v1/messages",
              {"roomId": room, "files" : ["https://png.pngtree.com/png-vector/20190409/ourlarge/pngtree-ics-file-document-icon-png-image_922637.jpg"]})
    # send_post("https://api.ciscospark.com/v1/messages",
    #           {"roomId": room, 'markdown': '<a href=\'https://goo.gl/maps/m9ss8AHU1Pr1eCAn7\'>Click here to access hospital location</a><br/>Your appointment details with hospital location is sent to your email as well.', "files": [
    #               "https://www.freepngimg.com/thumb/map/62873-map-computer-location-icon-icons-free-transparent-image-hd.png"]})
    send_post("https://api.ciscospark.com/v1/messages",
              {"roomId": room, "markdown": msg})

    email_msg = "Greetings,\n\nThank you for choosing Ivy. Please find your virtual appointment details via Cisco Webex below.\n\n" \
    "Webex meeting link: "+meeting_link+ \
    "\nMeeting Password: "+meeting_password+ \
    "\n\nRecord vitals using your smart wearable device before the appointment: "+bot_url+"/checkvitals" \
    "\n\nPlease join the meeting 5minutes ahead of schedule." \
    "\n\nThank you,\nIvy - Patient Help\n" \
    "For more information reach us at www.ivy.com"

    send_email_notification(patient_email,email_msg)
    return meeting_link


def virtual_doc():
    '''
    Function to send symptom request message
    :return: message
    '''
    msg = "Yes, for sure, but first can you please share the symptoms of the illness you are facing. <a href=\"https://github.com/rudreshveerappaji/Ivy-patient-help/blob/master/symptoms_list.txt\">Reference symptoms list.</a> <br/>"
    return msg


def connect_doc(room):
    '''
    Webex teams video call with a doctor
    :return: message
    '''
    msg = "Before we connect you to our Doctor/Nurse, Please authorize Ivy on your registered smart wearable device to fetch vitals."
    send_post("https://api.ciscospark.com/v1/messages",
              {"roomId": room, "markdown": msg})
    sleep(10)
    msg = "Good News!! Your vitals were fetched and shared with the Doctor/Nurse successfully"
    send_post("https://api.ciscospark.com/v1/messages",
              {"roomId": room, "markdown": msg})
    sleep(5)
    msg = "Based on your symptoms/vitals analysis and criticality of the illness, I'm connecting you to a nurse/doctor right away...<br/><br/>Searching for available nurse/doctor.....<br/><br/>"
    send_post("https://api.ciscospark.com/v1/messages",
              {"roomId": room, "markdown": msg})
    sleep(5)
    return msg


def notify_docs(payload):
    '''
    Notify docs when a call is established
    :return: response
    '''
    url = "https://api.ciscospark.com/v1/messages"

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text.encode('utf8'))


def schedule_meeting(start, end):
    '''
        Schedule webex meeting as per selection
        :return: response
    '''
    url = "https://api.ciscospark.com/v1/meetings"

    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': 'Bearer ' + user_token
    }

    payload = "{\"title\":\"Appointment with Dr. Abhi\",\"password\":\"abcd1234\",\"start\":\""+str(start)+"\",\"end\":\""+str(end)+"\",\"enabledAutoRecordMeeting\":\"false\",\"allowAnyUserToBeCoHost\":\"false\"}"
    print(payload)
    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    return response.json()

def send_email_notification(pat_email,message):
    '''
        Send email notification to the patient
        :return: none
    '''

    smtp_server = "smtp.gmail.com"
    sender_email = "ivy.patient.help.asic@gmail.com"
    receiver_email = pat_email
    password = email_password

    msg = EmailMessage()
    msg.set_content(message)

    msg['Subject'] = 'Appointment confirmation from Ivy - Patient Help'
    msg['From'] = sender_email
    msg['To'] = receiver_email

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(sender_email, password)
    server.send_message(msg)
    server.quit()
    return

setup_bot_webhook()

app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def teams_webhook():
    '''
    Main function
    :return: Boolean or message
    '''

    global patient_email, option, disease, score,patient_name
    if request.method == 'POST':
        count = 0
        webhook = request.get_json(silent=True)
        if webhook['data']['personEmail']!= bot_email:
            print(webhook)
        if "@webex.bot" not in webhook['data']['personEmail']:
            roomId = webhook['data']['roomId']
            result = send_get(
                'https://api.ciscospark.com/v1/messages/{0}'.format(webhook['data']['id']))
            in_message = result.get('text', '').lower()
            in_message = in_message.replace(bot_app_name.lower() + " ", '')
            if any(re.search(word,in_message) for word in ['help','assist', 'what can you do']):
                msg = help_me()
            elif any(re.search(word,in_message) for word in [r'\bhi\b','hello','wassup']):
                msg = greetings()
            elif any(word in in_message for word in ['i\'m','i am','my name is','im']):
                print(in_message)
                try:
                    patient_name = re.search('name\s\w+\s(\w+)',in_message).group(1)
                    patient_email = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', in_message)
                    patient_email = patient_email[0]
                except Exception as e:
                    msg = "Please enter all the required details.<br>" \
                          "Usage: My name is [name], email id [your email], patient id [your patient id]"
                    send_post("https://api.ciscospark.com/v1/messages",
                              {"roomId": webhook['data']['roomId'], "markdown": msg})
                    return
                print(patient_email)
                msg = "Welcome "+patient_name+" !! Thanks for sharing your details, here are the list of things that I can help you with. Start by asking any of the following:<br>" \
                      "- Book a virtual appointment.<br>" \
                      "- Here are my symptoms: {Your list of symptoms}.- <a href=\"https://github.com/rudreshveerappaji/Ivy-patient-help/blob/master/symptoms_list.txt\">Reference symptoms list.</a><br>" \
                      "- Connect to a doctor.<br>"
            elif any(word in in_message for word in ['appointment','book a time', 'book an appointment']):
                msg = "Sure!! Please select your desired slot from below available options to meet Doctor/Nurses\n\n " \
                      "<br><h4>Option 1: 02/Aug/2020 1pm</h4>\n\n" \
                      "<br><h4>Option 2: 02/Aug/2020 3pm</h4>\n\n" \
                      "<br><h4>Option 3: 04/Aug/2020 11am</h4>"
            elif any(word in in_message for word in ['option', 'i will select', 'I will go with']):
                option = re.findall(r'[1-3]', in_message)
                msg = None
                # Book Appointment and schedule webex meeting
                webex_meet = book_appointment(roomId,option[0], patient_email)
                if option.__eq__("1"):
                    slot = "02/Aug/2020 1pm"
                elif option.__eq__("2"):
                    slot = "02/Aug/2020 3pm"
                elif option.__eq__("3"):
                    slot = "04/Aug/2020 11am"
                print(disease,score,slot)
                print(webex_meet)
                payload = "{\n\"toPersonEmail\": \"abhr@cisco.com\",\n\"markdown\": \"[Learn more](https://adaptivecards.io) about Adaptive Cards.\",\n\"attachments\": [\n{\n\"contentType\": \"application/vnd.microsoft.card.adaptive\",\n\"content\": {\n\"type\": \"AdaptiveCard\",\n\"version\": \"1.0\",\n\"body\": [\n{\n\"type\": \"TextBlock\",\n\"text\": \"An appoinment is booked with you for patient "+patient_name+" for "+str(slot)+". Based on Machine Learning symptom analysis it seems that the patient is suffering from "+str(disease)+" with the accuracy of "+str(score)+". Thank you.\"\n}\n],\n\"actions\": [\n{\n\"type\": \"Action.OpenUrl\",\n\"title\": \"Webex Meeting Link\",\n\"url\":\""+str(webex_meet)+"\"\n}\n]\n}\n}\n]\n}"
                notify_docs(payload)
            elif any(re.search(word,in_message) for word in ['call a doctor', 'connect me to the doctor', 'talk to a doctor', 'connect me to a doctor', 'speak to a doctor']):
                msg = virtual_doc()
            elif any(re.search(word,in_message) for word in ['thank you', 'Bye', 'Cya', 'See you', 'thanks']):
                msg = "<p>Your most welcome &#128512;</p>"
            elif any(re.search(word,in_message) for word in ml.l1):
                num_symp = sum(word in in_message for word in  ml.l1)
                symptoms = in_message.split(',')
                disease, score = ml.NaiveBayes(symptoms)
                print("Disease = "+disease)
                print("Score = " + str(score))
                if disease in ml.critical_disease:
                    payload = "{\n\"toPersonEmail\": \"abhr@cisco.com\",\n\"markdown\": \"[Learn more](https://adaptivecards.io) about Adaptive Cards.\",\n\"attachments\": [\n{\n\"contentType\": \"application/vnd.microsoft.card.adaptive\",\n\"content\": {\n\"type\": \"AdaptiveCard\",\n\"version\": \"1.0\",\n\"body\": [\n{\n\"type\": \"TextBlock\",\n\"text\": \"Patient "+patient_name+" is waiting in your Webex Teams room, kindly connect. Based on Machine Learning symptom analysis it seems that the patient is suffering from "+str(disease)+" with the accuracy of "+str(score)+". Thank you.\"\n}\n],\n\"actions\": [\n{\n\"type\": \"Action.OpenUrl\",\n\"title\": \"Connect\",\n\"url\":\"http://0.0.0.0:8080/connect\"\n}\n]\n}\n}\n]\n}"
                    notify_docs(payload)
                    connect_doc(roomId)
                    msg = "<b>Dr Abhi</b> available now...<br/><a href=\""+bot_url+"/test\" target=\"_blank\">Click here to talk to your doctor over video</a>"
                else:
                    msg = "Based on your symptoms, I can schedule an appointment with a nurse/doctor at the earliest slot available.<br/>Would you want me to book an appointment?"
            elif in_message.startswith("repeat after me"):
                message = in_message.split('repeat after me ')[1]
                if len(message) > 0:
                    msg = "{0}".format(message)
                else:
                    msg = "I did not get that. Sorry!"
            else:
                msg = None
            if msg != None:
                send_post("https://api.ciscospark.com/v1/messages",
                                {"roomId": webhook['data']['roomId'], "markdown": msg})
        return "true"
    elif request.method == 'GET':
        message = "Ivy the Bot is up and running"
        return message


@app.route('/connect')
def addoc():
    '''
    Function for video call
    :return:
    '''
    f = open("guestToken.txt", "r")
    guest_token = f.read() #Fetch guest token
    print("bot guest - " +guest_token)
    return render_template("bot.html", data = [guest_token,"abhr@cisco.com"])

@app.route('/checkvitals')
def check_vitals():
    '''
    Function for video call
    :return:
    '''
    message = Markup("<h1>Vitals check Initiated, authorize access to Ivy on your smart wearable device.</h1>")
    flash(message)
    return render_template('vitals.html')

if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    # Run Bot
    app.run(host="0.0.0.0", port=8080)
