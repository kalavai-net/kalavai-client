"""
pip install aiohttp
"""
import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any

# Configuration
API_URL = "http://0.0.0.0:30617/v1/chat/completions"  # Replace with your OpenAI-compatible API URL
API_KEY = "sk-1234"  # Replace with your actual API key
MODEL = "qwen2.5-1.5b-instruct-q2_k.gguf"  # Replace with your model name
NUM_PARALLEL_CALLS = 1  # Change this to adjust number of parallel requests
NUM_REQUESTS = 1  # Total number of requests to make
PROMPT_TEMPLATE = "Explain the concept of {topic} in simple terms."
TOPICS = ["quantum computing", "machine learning", "neural networks", "artificial intelligence", "blockchain"]

# Optional: Add a delay between requests (in seconds) to avoid rate limiting
DELAY_BETWEEN_REQUESTS = 0.0  # Set to 0.1 or higher if needed

async def make_request(session: aiohttp.ClientSession, request_id: int, topic: str) -> Dict[str, Any]:
    """
    Make a single asynchronous HTTP request to the OpenAI-compatible API.
    """
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": PROMPT_TEMPLATE.format(topic=topic)}
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        start_time = time.time()
        async with session.post(API_URL, json=payload, headers=headers) as response:
            response.raise_for_status()
            result = await response.json()
            end_time = time.time()
            
            # Extract response details
            response_time = end_time - start_time
            token_count = result.get("usage", {}).get("total_tokens", 0)
            
            return {
                "request_id": request_id,
                "success": True,
                "response_time": response_time,
                "token_count": token_count,
                "response": result
            }
            
    except aiohttp.ClientError as e:
        end_time = time.time()
        return {
            "request_id": request_id,
            "success": False,
            "error": str(e),
            "response_time": end_time - start_time,
            "token_count": 0
        }
    except Exception as e:
        end_time = time.time()
        return {
            "request_id": request_id,
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "response_time": end_time - start_time,
            "token_count": 0
        }

async def run_concurrent_requests(num_parallel_calls: int, num_requests: int, topics: List[str]) -> List[Dict[str, Any]]:
    """
    Run multiple concurrent HTTP requests to the API.
    """
    print(f"Starting {num_requests} requests with {num_parallel_calls} parallel calls...")
    
    # Create a session for making HTTP requests
    async with aiohttp.ClientSession() as session:
        # Create a list of tasks
        tasks = []
        for i in range(num_requests):
            # Cycle through topics to avoid always using the same prompt
            topic = topics[i % len(topics)]
            task = make_request(session, i + 1, topic)
            tasks.append(task)
            
            # Add delay between requests if specified
            if DELAY_BETWEEN_REQUESTS > 0:
                await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Execute tasks with concurrency limit
        semaphore = asyncio.Semaphore(num_parallel_calls)
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        # Run tasks with bounded concurrency
        results = await asyncio.gather(*[bounded_task(task) for task in tasks])
        
        return results

def analyze_results(results: List[Dict[str, Any]]) -> None:
    """
    Analyze and print performance metrics.
    """
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    total_requests = len(results)
    success_rate = len(successful) / total_requests * 100
    avg_response_time = sum(r["response_time"] for r in successful) / len(successful) if successful else 0
    avg_tokens = sum(r["token_count"] for r in successful) / len(successful) if successful else 0
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Total requests: {total_requests}")
    print(f"Successful requests: {len(successful)} ({success_rate:.2f}%)")
    print(f"Failed requests: {len(failed)}")
    print(f"Average response time: {avg_response_time:.4f} seconds")
    print(f"Average tokens per response: {avg_tokens:.2f}")
    
    if failed:
        print("\nFailed requests details:")
        for result in failed:
            print(f"  Request {result['request_id']}: {result['error']}")
    
    # Show response time distribution
    response_times = [r["response_time"] for r in successful]
    if response_times:
        print(f"\nResponse time statistics:")
        print(f"  Min: {min(response_times):.4f}s")
        print(f"  Max: {max(response_times):.4f}s")
        print(f"  90th percentile: {sorted(response_times)[int(0.9 * len(response_times))]:.4f}s")

async def main():
    """
    Main function to run the test.
    """
    # You can change this value to adjust the number of parallel calls
    global NUM_PARALLEL_CALLS
    
    # Run the concurrent requests
    results = await run_concurrent_requests(NUM_PARALLEL_CALLS, NUM_REQUESTS, TOPICS)
    
    # Analyze and display results
    analyze_results(results)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())


    