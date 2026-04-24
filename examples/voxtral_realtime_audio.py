# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""
Minimal Gradio demo for real-time speech transcription using the vLLM Realtime API.

    python gradio-voxtral.py --url voxtral-realtime-default-vllm.spaces.kalavai.net/realtime

Use --share to create a public Gradio link.

Requirements: websockets, numpy, gradio, pybase64
"""

import argparse
import asyncio
import json
import queue
import threading

import gradio as gr
import numpy as np
import pybase64 as base64
import websockets

SAMPLE_RATE = 16_000

# Global state
audio_queue: queue.Queue = queue.Queue()
transcription_text = ""
is_running = False
ws_url = ""
model = ""


async def websocket_handler():
    """Connect to WebSocket and handle audio streaming + transcription."""
    global transcription_text, is_running

    try:
        async with websockets.connect(ws_url) as ws:
            print("WebSocket connected")
            
            # Wait for session.created
            await ws.recv()

            # Validate model
            await ws.send(json.dumps({"type": "session.update", "model": model}))

            # Signal ready
            await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))

            async def send_audio():
                while is_running:
                    try:
                        chunk = await asyncio.get_event_loop().run_in_executor(
                            None, lambda: audio_queue.get(timeout=0.5)
                        )
                        await ws.send(
                            json.dumps(
                                {"type": "input_audio_buffer.append", "audio": chunk}
                            )
                        )
                    except queue.Empty:
                        # Brief pause to prevent busy loop
                        await asyncio.sleep(0.1)
                        continue
                    except Exception as e:
                        print(f"Error sending audio: {e}")
                        break

            async def receive_transcription():
                global transcription_text
                try:
                    async for message in ws:
                        if not is_running:
                            break
                        data = json.loads(message)
                        if data.get("type") == "transcription.delta":
                            transcription_text += data["delta"]
                except websockets.exceptions.ConnectionClosed:
                    pass
                except Exception as e:
                    print(f"Error receiving transcription: {e}")

            await asyncio.gather(send_audio(), receive_transcription())
            
    except Exception as e:
        print(f"WebSocket connection error: {e}")
    finally:
        is_running = False


def start_websocket():
    """Start WebSocket connection in background thread."""
    global is_running
    is_running = True
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(websocket_handler())
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        loop.close()




def process_audio(audio):
    """Process incoming audio and queue for streaming."""
    global transcription_text, is_running
    
    if audio is None:
        return transcription_text
    
    # Auto-start WebSocket if not running and audio is detected
    if not is_running:
        print("Starting transcription service...")
        thread = threading.Thread(target=start_websocket, daemon=True)
        thread.start()
        # Give it a moment to start
        import time
        time.sleep(0.5)

    sample_rate, audio_data = audio

    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)

    # Normalize to float
    if audio_data.dtype == np.int16:
        audio_float = audio_data.astype(np.float32) / 32767.0
    else:
        audio_float = audio_data.astype(np.float32)

    # Resample to 16kHz if needed
    if sample_rate != SAMPLE_RATE:
        num_samples = int(len(audio_float) * SAMPLE_RATE / sample_rate)
        audio_float = np.interp(
            np.linspace(0, len(audio_float) - 1, num_samples),
            np.arange(len(audio_float)),
            audio_float,
        )

    # Convert to PCM16 and base64 encode
    pcm16 = (audio_float * 32767).astype(np.int16)
    b64_chunk = base64.b64encode(pcm16.tobytes()).decode("utf-8")
    audio_queue.put(b64_chunk)

    return transcription_text


# Gradio interface
with gr.Blocks(title="Real-time Speech Transcription") as demo:
    gr.Markdown("# Real-time Speech Transcription")
    gr.Markdown("Click the **record** button below and speak into your microphone. The transcription will start automatically.")

    audio_input = gr.Audio(sources=["microphone"], streaming=True, type="numpy")
    transcription_output = gr.Textbox(label="Transcription", lines=5)

    audio_input.stream(
        process_audio, inputs=[audio_input], outputs=[transcription_output]
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Realtime WebSocket Transcription with Gradio"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mistralai/Voxtral-Mini-4B-Realtime-2602",
        help="Model that is served and should be pinged.",
    )
    parser.add_argument(
        "--url", type=str, default="localhost", help="vLLM server url"
    )
    parser.add_argument(
        "--share", action="store_true", help="Create public Gradio link"
    )
    args = parser.parse_args()

    ws_url = f"ws://{args.url}/v1/realtime"
    model = args.model
    demo.launch(share=args.share)