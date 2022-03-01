import websockets
import asyncio
from watchgod import awatch

PORT = 8888
print("Starting server on port", PORT)

connected = set()

async def watch():
    async for changes in awatch('./static/protected_images/'):
            changeArr = str(changes).split(',')
            action = changeArr[0][3:-4]
            path = changeArr[1][2:-3]
            for conn in connected:
                await conn.send('{"action": "' + action + '", "path": "' + path + '"}')

async def echo(websocket, path):
    connected.add(websocket)
    try:
        async for message in websocket:
            print("Received:", message)
            for conn in connected:
                if conn != websocket:
                    await conn.send(message)
    except websockets.ConnectionClosed as e:
        print("Connection closed:", e.code, e.reason)
    finally:
        connected.remove(websocket)

if __name__ == "__main__":

    start_server = websockets.serve(echo, "localhost", PORT)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_until_complete(watch())
    asyncio.get_event_loop().run_forever()  
