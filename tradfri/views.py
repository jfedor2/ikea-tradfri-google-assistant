# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings

from oauth2_provider.decorators import protected_resource

import json
import subprocess

COAP_CLIENT_PUT = [
    settings.COAP_CLIENT,
    '-m',
    'put',
    '-u',
    'Client_identity',
    '-k',
    settings.IKEA_SECRET,
    '-e',
    '{{ "3311": [{{ "{command}": {state} }}] }}',
    'coaps://' + settings.GATEWAY_ADDRESS + ':5684/15001/{id_}',
]

COAP_CLIENT_GET = [
    settings.COAP_CLIENT,
    '-m',
    'get',
    '-u',
    'Client_identity',
    '-k',
    settings.IKEA_SECRET,
    'coaps://' + settings.GATEWAY_ADDRESS + ':5684/{path}',
]

@csrf_exempt
@protected_resource()
def endpoint(request):
    data = json.loads(request.body)
    intent = data['inputs'][0]['intent']
    response = {
        'action.devices.SYNC': sync_action,
        'action.devices.QUERY': query_action,
        'action.devices.EXECUTE': execute_action,
    }[intent](data)
    response['requestId'] = data['requestId']
    return HttpResponse(json.dumps(response))

def sync_action(data):
    devices = [
        {
            "id": unicode(light['9003']),
            "type": "action.devices.types.LIGHT",
            "traits": [
                "action.devices.traits.OnOff",
                "action.devices.traits.Brightness",
                "action.devices.traits.ColorTemperature",
            ],
            "name": {
                "defaultNames": [light["3"]["1"]],
                "name": light["9001"].lower() + ' light',
                "nicknames": [ light["9001"].lower() + ' light' ],
            },
            "willReportState": False,
        }
        for light in ikea_get_lights()
    ]

    return { 'payload': { 'devices': devices } }

def query_action(data):
    devices = {}

    for device in data["inputs"][0]["payload"]["devices"]:
        devices[device["id"]] = ikea_get_light(device["id"])

    return { "payload": { "devices": devices } }

def execute_action(data):
    results = []
    for command in data["inputs"][0]["payload"]["commands"]:
        for device in command["devices"]:
            for execution in command["execution"]:
                if execution["command"] == 'action.devices.commands.OnOff':
                    ikea_set_light(device["id"], execution["params"]["on"])
                if execution["command"] == 'action.devices.commands.BrightnessAbsolute':
                    ikea_set_brightness(device["id"], int(254*int(execution["params"]["brightness"])/100))
                results.append({"ids": [device["id"]], "status": "SUCCESS"})

    return { "payload": { "commands": results } }

def ikea_get_lights():
    devices = [ ikea_get_device(id_) for id_ in json.loads(subprocess.check_output([x.format(path='15001') for x in COAP_CLIENT_GET])) ]
    return [ device for device in devices if device['5750'] == 2 ]

def ikea_get_light(id_):
    device_info = ikea_get_device(id_)
    return {
        "online": True,
        "on": device_info["3311"][0]["5850"] == 1,
        "brightness": 0 if device_info["3311"][0]["5850"] == 0 else int(100*device_info["3311"][0]["5851"]/254),
    } if device_info["9019"] == 1 else {
        "online": True, # :-/
    }

def ikea_get_device(id_):
    return json.loads(subprocess.check_output([x.format(path='15001/{}'.format(id_)) for x in COAP_CLIENT_GET]))

def ikea_set_light(id_, state):
    subprocess.call([x.format(id_=id_, state=1 if state else 0, command=5850) for x in COAP_CLIENT_PUT])

def ikea_set_brightness(id_, state):
    subprocess.call([x.format(id_=id_, state=state, command=5851) for x in COAP_CLIENT_PUT])
