"""
TTS inference example

Model for the task: Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice

Requires:

pip install openai requests

--omni --enforce-eager --trust-remote-code --max-model-len 4000
"""
import time

from openai import OpenAI


API_URL = "http://100.1.0.1"
API_KEY = "dummy"
MODEL_ID = "qwen/qwen-audio-3.0-tts-flash"


input_texts = [
    "Hi everyone. As a Senior Lecturer in AI on the Industry Track, my background bridges founding and exiting AI startups with directing enterprise AI, such as my grassroots strategy work in Bayer and AI implementation at Springer.​ I live in these tools daily. Tools like Claude, Perplexity, and Notebook LM kept me afloat during my Cambridge MBA while running a startup. On the developer side, I deploy end-to-end LLMs and agentic AI systems. I built this presentation using Gemini to structure against the brief, open source text-to-speech for the voice over, and Notebook LM to cross-reference job descriptor and University policy—refining every output manually. ​ My core rule for AI is simple: LLMs never have the final say. Whether through critical human thinking or code guardrails, strict verification and data protection are non-negotiable. That is the responsible, risk-aware leadership I bring to this role.​",
    "AI brings real threats to higher education: academic dishonesty, overreliance that weakens critical skills and a growing digital divide. But it also unlocks immense value through personalized learning and reduced friction for staff. ​To lead this across our faculty, we must avoid single-vendor lock-in and top-down decision making. Tech moves too fast to lock MMU into a single ecosystem. ​Instead, we drive adoption from the bottom up. We build confidence through departmental 'AI Champions,' dedicated trial budgets, supported by advisory hubs. We foster innovation with hackathons opened to staff and students, with themes tackling big challenges such as student dishonesty and staff overload.​",
    "Beyond tool adoption, MMU has a strategic opportunity to generate value for the wider community and shape the UK's AI sovereignty path. ​Industry compute is scarce and expensive, and local communities often feel left behind by technology that extracts more than it gives. Yet MMU sits on a massive pool of underutilised desktops and workstations across departments. Having pooled infrastructure in past roles, I know we can turn this idle capacity into an engine for research and teaching. ​By activating our compute, we can self-host secure, open-source AI tools—reducing cloud costs, freeing researchers from grant-funding delays, and placing computing power directly into the hands of our students, staff, and regional partners.",
    "AI is changing education. Let’s lead it with an evidence-based, grassroots culture that empowers our people, unlocks our internal infrastructure, and positions MMU at the heart of the UK's digital future."
]


# Generate speech with style
client = OpenAI(base_url=f"{API_URL}/v1", api_key=API_KEY)

for i, text in enumerate(input_texts):
    response = client.audio.speech.create(
        model=MODEL_ID,
        voice="loongjohn",
        input=text,
        instructions="Speak with enthusiasm but with a professional tone.",
        response_format="mp3"
    )
    response.stream_to_file(f"output_{i}.mp3")
    print("Speech generated for input text:", i)

print("Output saved to output_[x].mp3")