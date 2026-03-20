import asyncio
import websockets


async def test_ws():
    uri = "ws://localhost:8000/ws/seed-progress"
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello server!")
        response = await websocket.recv()
        print("Received:", response)


asyncio.run(test_ws())
