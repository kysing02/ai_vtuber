import asyncio
import json
import websockets
import uuid
import os

class VTSAdapter:
    hotkeys = {
        1: "Relaxed",
        2: "Shy",
        3: "Excited",
        4: "Angry",
        5: "Sad"
    }
    
    def __init__(self, host="localhost", port=8001):
        self.uri = f"ws://{host}:{port}"
        self.session_id = None
        self.ws = None
        self.authenticated = False
        self.plugin_name = "AI VTuber"
        self.plugin_developer = "NonStopBeat"
        self.token = os.getenv("VTS_AUTHENTICATION_TOKEN")

    async def connect_auth(self):
        if await self.__connect():
            if await self.__authenticate():
                return True

    async def __connect(self):
        try:
            self.ws = await websockets.connect(self.uri)
            asyncio.create_task(self.send_heartbeat())
            print("Connected to VTube Studio.")
            return True
        except ConnectionRefusedError:
            print("Error: Could not connect to VTube Studio. Make sure it's running and the API is enabled.")
            return False
        return True

    async def __authenticate(self):
        auth_request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "AuthenticationRequest",
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": self.plugin_name,
                "pluginDeveloper": self.plugin_developer,
                "authenticationToken": self.token if self.token else ""
            }
        }
        await self.ws.send(json.dumps(auth_request))
        auth_response = json.loads(await self.ws.recv())
        if auth_response["data"].get("authenticated"):
            print("Authentication successful.")
            self.authenticated = True
            self.session_id = str(uuid.uuid4())
            return True
        else:
            print("Authentication failed.", auth_response)
            return False

    async def trigger_hotkeys(self, hotkey_name=None):
        """
        Triggers specified hotkey by name.
        
        :param hotkey_name: The name of the hotkey to trigger (e.g., "Relaxed"). 
                            If None, triggers all hotkeys.
        """
        print(hotkey_name, "triggered.")
        if hotkey_name:
            # Find the hotkey ID by name
            hotkey_id = next((key for key, name in self.hotkeys.items() if name == hotkey_name), None)
            if hotkey_id:
                request = {
                    "apiName": "VTubeStudioPublicAPI",
                    "apiVersion": "1.0",
                    "requestID": f"HotkeyRequest_{hotkey_id}",
                    "messageType": "HotkeyTriggerRequest",
                    "data": {
                        "hotkeyID": hotkey_name,
                        "excludedParameters": ["MouthOpen", "MouthForm"]
                    }
                }
                await self.ws.send(json.dumps(request))
                res = await self.ws.recv()
                print(f"Triggered hotkey {hotkey_id}: {hotkey_name}")
            else:
                print(f"Hotkey '{hotkey_name}' not found.")

    async def send_heartbeat(self):
        while True:
            await asyncio.sleep(30)  # Adjust interval if needed
            try:
                await self.ws.ping()
            except Exception as e:
                print(f"Heartbeat failed: {e}")
                break

    async def close(self):
        if self.ws:
            await self.ws.close()
            print("Connection to VTube Studio closed.")

async def main():
    vts_adapter = VTSAdapter()
    if await vts_adapter.connect_auth():
        while True:
            expression = input("Enter an expression to change to (or 'exit' to quit): ")
            if expression.lower() == "exit":
                break
            await vts_adapter.trigger_hotkeys(expression)

    await vts_adapter.close()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())