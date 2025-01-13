"""Requires pip install openai
"""
import time

from openai import OpenAI


PROMPTS = [
    "The capital of France is",
    "The moon is made of"
]
MAX_TOKENS = 100
# Modify OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "NONE"
openai_api_base = "http://100.10.0.5:32169/v1"

if __name__ == "__main__": 
    client = OpenAI(
        api_key=openai_api_key,
        base_url=openai_api_base,
    )
    t = time.time()
    completion = client.completions.create(
        model="Qwen/Qwen2.5-1.5B-Instruct",
        prompt=PROMPTS,
        max_tokens=MAX_TOKENS)

    for prompt, choice in zip(PROMPTS, completion.choices):
        print(f"Prompt: ", prompt)
        print(choice.text)
        print("-------------------")

    total_time = time.time()-t
    print(f">> Total inference time {total_time:.2f} seconds ({total_time/len(PROMPTS):.2f} per prompt)")
