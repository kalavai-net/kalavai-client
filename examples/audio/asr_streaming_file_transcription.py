"""
ASR inference example using realtime API for streaming

Requires:

pip install httpx websockets pybase64
"""

import asyncio
import httpx
import json
import websockets
import pybase64 as base64
import time

MODEL_ID = "Qwen/Qwen3-ASR-1.7B"
API_URL = "qwen-asr-test-default-vllm.spaces.kalavai.net"
WS_URL = f"wss://{API_URL}/v1/realtime"

SAMPLE_RATE = 16_000


async def stream_audio_file(ws, audio_url: str, chunk_size: int = 12000):
    """Download audio file and stream it in chunks to the WebSocket."""
    # Download audio file
    print(f"Downloading audio from {audio_url}...")
    audio_response = httpx.get(audio_url)
    audio_data = audio_response.content
    
    # For WAV files, we need to parse and extract PCM data
    # For simplicity, we'll send the raw audio data in chunks
    # In production, you'd want to properly decode the audio format
    
    print(f"Streaming {len(audio_data)} bytes of audio...")
    
    # Stream in chunks
    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i:i + chunk_size]
        # Base64 encode the chunk
        b64_chunk = base64.b64encode(chunk).decode("utf-8")
        
        # Send to WebSocket
        await ws.send(
            json.dumps(
                {"type": "input_audio_buffer.append", "audio": b64_chunk}
            )
        )
        
        # Small delay to simulate real-time streaming
        await asyncio.sleep(0.01)
    
    # Signal that we're done sending audio
    await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
    print("Audio streaming complete")


async def realtime_transcription(audio_url: str):
    """Perform streaming transcription using the realtime API."""
    transcription = ""
    
    try:
        async with websockets.connect(WS_URL) as ws:
            print("WebSocket connected")
            
            # Wait for session.created
            session_info = await ws.recv()
            print(f"Session created: {session_info}")
            
            # Validate model
            await ws.send(json.dumps({"type": "session.update", "model": MODEL_ID}))
            
            # Start streaming audio
            await stream_audio_file(ws, audio_url)
            
            # Receive transcription
            print("Receiving transcription...")
            async for message in ws:
                data = json.loads(message)
                
                if data.get("type") == "transcription.delta":
                    delta = data.get("delta", "")
                    transcription += delta
                    print(delta, end="", flush=True)
                
                elif data.get("type") == "transcription.done":
                    print("\nTranscription complete")
                    break
                
                elif data.get("type") == "error":
                    print(f"\nError: {data.get('error', 'Unknown error')}")
                    break
            
            return transcription
            
    except Exception as e:
        print(f"\nWebSocket error: {e}")
        return transcription


async def main():
    audio_url = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-ASR-Repo/asr_en.wav"
    
    t = time.time()
    transcription = await realtime_transcription(audio_url)
    elapsed = time.time() - t
    
    print(f"\n\nFinal transcription: {transcription}")
    print(f"Time: {elapsed:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
