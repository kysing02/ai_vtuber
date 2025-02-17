import asyncio
import json
import websockets
import uuid
import os
from dotenv import load_dotenv
import logging

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
        self.heartbeat_running = False
        self.recv_lock = asyncio.Lock()
        self.loop = asyncio.get_event_loop()

    async def connect_auth(self):
        """VTube Studioの接続と認証を行う。"""
        if await self.__connect():
            if await self.__authenticate():
                return True
        return False

    async def __connect(self):
        """Establish a WebSocket connection to VTube Studio."""
        try:
            self.ws = await websockets.connect(self.uri)
            logging.info("Connected to VTube Studio.")
            return True
        except ConnectionRefusedError:
            logging.error("Could not connect to VTube Studio. Make sure it's running and the API is enabled.")
            return False

    async def __authenticate(self):
        """Authenticate with VTube Studio."""
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
            logging.info("Authentication successful.")
            self.authenticated = True
            self.session_id = str(uuid.uuid4())
            # Start the heartbeat task
            # self.heartbeat_task = self.loop.create_task(self.send_heartbeat())
            return True
        else:
            logging.error("Authentication failed.", auth_response)
            return False

    async def trigger_hotkeys(self, hotkey_name=None):
        """
        Triggers specified hotkey by name.
        
        :param hotkey_name: The name of the hotkey to trigger (e.g., "Relaxed"). 
                            If None, triggers all hotkeys.
        """
        if hotkey_name and hotkey_name in self.hotkeys.values():
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "messageType": "HotkeyTriggerRequest",
                "data": {
                    "hotkeyID": hotkey_name
                }
            }
            try:
                await self.ws.send(json.dumps(request))
                async with self.recv_lock:  # Use the lock to ensure exclusive access to recv()
                    res = await self.ws.recv()
                logging.info(f"Triggered hotkey: {hotkey_name}")
            except websockets.exceptions.ConnectionClosed:
                logging.warning("WebSocket connection closed. Reconnecting...")
                await self.loop.create_task(self.reconnect())
            except asyncio.TimeoutError:
                logging.error("WebSocket response timed out.")
        else:
            logging.warning(f"Hotkey '{hotkey_name}' not found.")

    async def send_heartbeat(self):
        logging.info("Heartbeat sent.")
        """Send periodic heartbeat messages to keep the connection alive."""
        self.heartbeat_running = True
        while self.authenticated and self.heartbeat_running:
            try:
                await self.ws.ping()
                # heartbeat_request = {
                #     "apiName": "VTubeStudioPublicAPI",
                #     "apiVersion": "1.0",
                #     "messageType": "CurrentModelRequest",
                #     "data": {}
                # }
                # await self.ws.send(json.dumps(heartbeat_request))
                # async with self.recv_lock:  # Use the lock to ensure exclusive access to recv()
                #     await self.ws.recv()
                # logging.info("Heartbeat sent.")
                await asyncio.sleep(5)  # 5秒ごとに送信
            except Exception as e:
                logging.error(f"Heartbeat failed: {e}")
                self.heartbeat_running = False  # Stop thread
                self.authenticated = False
                await self.reconnect()
                break  # 再接続後に新しいタスクを作成するため、ここで終了

    async def reconnect(self):
        """Reconnect to VTube Studio if the connection is lost."""
        logging.warning("Attempting to reconnect...")

        # if self.heartbeat_task:
        #     self.heartbeat_task.cancel()  # Cancel the old heartbeat task
        # await self.close()

        for _ in range(3):  # 最大3回リトライ
            if await self.connect_auth():
                logging.info("Reconnection successful!")
                return
            logging.warning("Retrying connection...")
            await asyncio.sleep(3)

        logging.error("Failed to reconnect after 3 attempts.")

    async def close(self):
        """Close the WebSocket connection."""
        self.heartbeat_running = False
        if self.ws:
            await self.ws.close()
            logging.info("Connection to VTube Studio closed.")
        self.authenticated = False

async def main():
    """Main function to run the VTSAdapter."""
    vts_adapter = VTSAdapter()
    if await vts_adapter.connect_auth():
        while True:
            expression = input("Enter an expression to change to (or 'exit' to quit): ")
            if expression.lower() == "exit":
                break
            await vts_adapter.trigger_hotkeys(expression)

    await vts_adapter.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    asyncio.run(main())