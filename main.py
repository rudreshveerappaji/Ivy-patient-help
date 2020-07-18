#!/usr/bin/env python
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

import base64
import os
from random import randrange

import jwt
from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv('config/credentials.env')

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def home():
    '''
    Main function
    :return: Home page - index.html
    '''
    guest_token = generate_guest_token()
    print(guest_token.decode("UTF-8"))
    return render_template("index.html",data=[guest_token.decode("UTF-8"),"patienthelp@webex.bot"])


def generate_guest_token():
    '''
    Generate guest user token using guest issuer app
    :return: token
    '''
    print(os.getenv('GUEST_ISSUER_SECRET'))
    random_user = randrange(10000, 20000, 2)
    payload = {
        "sub": str(random_user), #Guest User
        "name": "Patient",
        "iss": os.getenv('GUEST_ISSUER_ID'), #Guest Issuer APP ID
        "exp": "1627776000"  #08/01/2021 @ 12:00am (UTC)  #Expiry date of Guest Token in UNIX timestamp
    }
    key = os.getenv('GUEST_ISSUER_SECRET')  #Guest Issuer Secret
    encoded = jwt.encode(payload, base64.b64decode(key), headers={
        "typ": "JWT",
        "alg": "HS256"
    })

    with open("guestToken.txt", 'w') as filetowrite:
        filetowrite.write(str(encoded.decode("UTF-8")))
    filetowrite.close()
    
    return encoded

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)