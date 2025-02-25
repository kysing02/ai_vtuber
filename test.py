import requests

url = "http://localhost:8001"
data = {
    "apiName": "VTubeStudioPublicAPI",
    "apiVersion": "1.0",
    "requestID": "SomeID",
    "messageType": "AuthenticationTokenRequest",
    "data": {
        "pluginName": "AI VTuber",
        "pluginDeveloper": "NonStopBeat"
    }
}

response = requests.post(url, json=data)
print(response.text)
