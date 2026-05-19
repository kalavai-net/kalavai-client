"""
pip install aiohttp wonderwords
"""
import asyncio
import aiohttp
import argparse
import json
import time
import signal
from typing import List, Dict, Any

import wonderwords

r = wonderwords.RandomWord()


# Configuration

API_URL = "https://mistral-vllm-default-vllm.spaces.kalavai.net/v1/chat/completions" #"https://testme-default-litellm.spaces.kalavai.net/v1" #"https://api.cogenai.kalavai.net/v1" #"https://api.cogenai.kalavai.net/v1"  # Replace with your OpenAI-compatible API URL
API_KEY = ""  # Replace with your actual API key
DEFAULT_MODEL = "unsloth/Mistral-Small-3.2-24B-Instruct-2506-FP8" #"Hastagaras/Jamet-8B-L3-MK.V-Blackroot" #mistralai/Mistral-Nemo-Instruct-2407"  # Replace with your model name

NUM_PARALLEL_CALLS = 100  # Change this to adjust number of parallel requests
NUM_REQUESTS = 5 # Total number of requests to make
INPUT_TOKENS = 900 
TOKEN_TO_WORD_RATIO = 1.5 # uses 1.5 tokens per word estimate
MAX_OUTPUT_TOKENS = 50

# Global flag for graceful shutdown
shutdown_flag = False

async def make_request(session: aiohttp.ClientSession, request_id: int, topic: str, model: str) -> Dict[str, Any]:
    """
    Make a single asynchronous HTTP request to the OpenAI-compatible API.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": topic}
        ],
        "max_tokens": MAX_OUTPUT_TOKENS,
        "temperature": 1.0
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
            token_count = result.get("usage", {}).get("total_tokens", 0) - result.get("usage", {}).get("prompt_tokens", 0)

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

async def run_concurrent_requests(num_parallel_calls: int, num_requests: int, model: str, request_offset: int = 0) -> List[Dict[str, Any]]:
    """
    Run multiple concurrent HTTP requests to the API.
    """
    print(f"Starting {num_requests} requests with {num_parallel_calls} parallel calls...")
    
    # Create a session for making HTTP requests
    async with aiohttp.ClientSession() as session:
        # Create a list of tasks
        tasks = []
        for i in range(num_requests):
            # Random sentences generated
            topic = " ".join([r.word() for _ in range(int(INPUT_TOKENS/TOKEN_TO_WORD_RATIO))])
            task = make_request(session, request_offset + i + 1, topic, model)
            tasks.append(task)
        
        # Execute tasks with concurrency limit
        semaphore = asyncio.Semaphore(num_parallel_calls)
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        # Run tasks with bounded concurrency
        results = await asyncio.gather(*[bounded_task(task) for task in tasks])
        
        return results

def analyze_results(results: List[Dict[str, Any]], total_time: float, show_details: bool = True) -> Dict[str, Any]:
    """
    Analyze and print performance metrics.
    Returns a dictionary with summary statistics.
    """
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    total_requests = len(results)
    success_rate = len(successful) / total_requests * 100 if total_requests > 0 else 0
    avg_response_time = sum(r["response_time"] for r in successful) / len(successful) if successful else 0
    total_tokens = sum(r["token_count"] for r in successful)
    avg_tokens = total_tokens / len(successful) if successful else 0
    avg_tokens_per_second = avg_tokens / avg_response_time if avg_response_time > 0 else 0
    total_tokens_per_second = total_tokens / total_time if total_time > 0 else 0
    
    if show_details:
        print("\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        print(f"Total requests: {total_requests}")
        print(f"Successful requests: {len(successful)} ({success_rate:.2f}%)")
        print(f"Failed requests: {len(failed)}")
        print(f"Average response time: {avg_response_time:.4f} seconds")
        print(f"Average tokens per response: {avg_tokens:.2f}")
        print(f"Average t/s: {avg_tokens_per_second:.2f} t/s")
        print(f"Total t/s: {total_tokens_per_second:.2f} t/s")
        
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
    
    return {
        "total": total_requests,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": success_rate,
        "avg_response_time": avg_response_time,
        "avg_tokens": avg_tokens,
        "avg_t_per_s": avg_tokens_per_second
    }

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global shutdown_flag
    print("\n\nShutting down gracefully... (Press Ctrl+C again to force exit)")
    shutdown_flag = True

async def run_continuous_requests(
    num_parallel_calls: int,
    num_requests_per_batch: int,
    model: str,
    interval: float
) -> None:
    """
    Run continuous requests at specified intervals.
    """
    global shutdown_flag
    all_results = []
    batch_number = 0
    total_requests = 0
    
    print(f"Running in continuous mode:")
    print(f"  Model: {model}")
    print(f"  Requests per batch: {num_requests_per_batch}")
    print(f"  Parallel calls: {num_parallel_calls}")
    print(f"  Interval: {interval} seconds")
    print(f"  Press Ctrl+C to stop\n")
    total_time = time.time()

    try:
        while not shutdown_flag:
            
            batch_number += 1
            print(f"\n[Batch {batch_number}] Starting at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Run a batch of requests
            batch_results = await run_concurrent_requests(
                num_parallel_calls,
                num_requests_per_batch,
                model,
                request_offset=total_requests
            )
            
            all_results.extend(batch_results)
            total_requests += len(batch_results)
            
            # Analyze this batch
            batch_stats = analyze_results(batch_results, total_time=time.time()-total_time, show_details=False)
            print(f"[Batch {batch_number}] Completed: {batch_stats['successful']}/{batch_stats['total']} successful, "
                  f"avg response time: {batch_stats['avg_response_time']:.4f}s")
            
            # Overall statistics
            overall_stats = analyze_results(all_results, total_time=time.time()-total_time, show_details=False)
            print(f"[Overall] Total: {overall_stats['total']} requests, "
                  f"Success rate: {overall_stats['success_rate']:.2f}%, "
                  f"Avg response time: {overall_stats['avg_response_time']:.4f}s")
            
            if shutdown_flag:
                break
            
            # Wait for the specified interval
            print(f"Waiting {interval} seconds until next batch...")
            await asyncio.sleep(interval)
            
    except KeyboardInterrupt:
        shutdown_flag = True
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    analyze_results(all_results, total_time=time.time()-total_time, show_details=True)

async def main():
    """
    Main function to run the test.
    """
    parser = argparse.ArgumentParser(
        description="Send parallel requests to an OpenAI-compatible API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run 10 requests with default model
  python service_requests.py --model "gpt-4"
  
  # Run continuous requests every 5 seconds
  python service_requests.py --model "gpt-4" --continuous --interval 5
  
  # Run continuous with custom batch size
  python service_requests.py --model "gpt-4" --continuous --interval 10 --num-requests 20
        """
    )
    
    parser.add_argument(
        "--model",
        dest="model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Model ID to use (default: {DEFAULT_MODEL})"
    )
    
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run requests continuously at specified intervals"
    )
    
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Interval in seconds between batches when using --continuous (default: 5.0)"
    )
    
    parser.add_argument(
        "--num-requests",
        type=int,
        default=NUM_REQUESTS,
        help=f"Number of requests per batch (default: {NUM_REQUESTS})"
    )
    
    parser.add_argument(
        "--num-parallel",
        type=int,
        default=NUM_PARALLEL_CALLS,
        help=f"Number of parallel calls (default: {NUM_PARALLEL_CALLS})"
    )
    
    args = parser.parse_args()
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    if args.continuous:
        # Run in continuous mode
        await run_continuous_requests(
            num_parallel_calls=args.num_parallel,
            num_requests_per_batch=args.num_requests,
            model=args.model,
            interval=args.interval
        )
    else:
        # Run single batch
        total_time = time.time()
        print(f"Model: {args.model}")
        results = await run_concurrent_requests(
            args.num_parallel,
            args.num_requests,
            args.model
        )
        analyze_results(results, total_time=time.time()-total_time)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
