"""
More info: https://github.com/petals-infra/chat.petals.dev

Required: pip install websockets
"""
import time
import json
import websockets
import asyncio


URL = "192.168.68.67:31220"
MODEL_NAME = "bigscience/bloom-3b"


async def ws_generate(text, max_length=100, temperature=0.1):
    async with websockets.connect(f"ws://{URL}/api/v2/generate") as websocket:
        try:
            await websocket.send(
                json.dumps({"model": MODEL_NAME, "type": "open_inference_session", "max_length": max_length})
            )
            response = await websocket.recv()
            result = json.loads(response)

            if result["ok"]:
                await websocket.send(
                    json.dumps({
                        "type": "generate",
                        "model": MODEL_NAME,
                        "inputs": text,
                        "max_length": max_length,
                        "temperature": temperature
                    })
                )
                response = await websocket.recv()
                return json.loads(response)
            else:
                return response
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    t = time.time()
    output = asyncio.get_event_loop().run_until_complete(
        ws_generate(text="Tell me a story: ")
    )
    final_time = time.time() - t
    print(f"[{final_time:.2f} secs]", output)
    print(f"{output['token_count'] / final_time:.2f}", "tokens/s")
