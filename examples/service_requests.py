"""
pip install aiohttp
"""
import asyncio
import aiohttp
import argparse
import json
import time
import signal
from typing import List, Dict, Any

# Configuration
API_URL = "http://51.159.177.196:30528/v1/chat/completions" #"https://api.cogenai.kalavai.net/v1/chat/completions"  # Replace with your OpenAI-compatible API URL
API_KEY = "sk-25021984"  # Replace with your actual API key
DEFAULT_MODEL = "Qwen/Qwen3-4B"  # Default model name
NUM_PARALLEL_CALLS = 100  # Change this to adjust number of parallel requests
NUM_REQUESTS = 100  # Total number of requests to make
MAX_OUTPUT_TOKENS = 250
PROMPT_TEMPLATE = "Answer the following question: {topic}"

# Global flag for graceful shutdown
shutdown_flag = False
TOPICS = [
    "How would you describe the culture and lifestyle in France?",
    "In what ways has Einstein’s theory of relativity influenced modern science and technology?",
    "Why is gold considered valuable both scientifically and economically?",
    "What makes Mars a strong candidate for future human exploration?",
    "How did George Washington shape the early years of the United States?",
    "Why are whales considered important to marine ecosystems?",
    "How do the continents of Earth differ in terms of climate and biodiversity?",
    "Why is mathematics considered the foundation of science?",
    "How has Shakespeare’s 'Romeo and Juliet' influenced literature and popular culture?",
    "Why is photosynthesis essential for life on Earth?",
    "What were the major consequences of World War II on global politics?",
    "How is diamond used in both industry and jewelry?",
    "Why is the Mona Lisa regarded as one of the most famous paintings in the world?",
    "How does oxygen support human life and biological processes?",
    "What challenges do climbers face when scaling Mount Everest?",
    "How has Japan’s culture influenced its economic growth and global presence?",
    "Why is the Pacific Ocean important for world trade and climate?",
    "How did the moon landing change humanity’s view of space exploration?",
    "Why is the cheetah considered a unique species among big cats?",
    "How does water’s boiling point change with altitude, and why?",
    "Why is the human heart vital to overall health and survival?",
    "How has ice hockey shaped Canadian national identity?",
    "How did the invention of the telephone transform communication?",
    "Why is the number two considered the first prime number?",
    "How has the Chinese language influenced culture and global communication?",
    "Why is Canberra the capital of Australia instead of Sydney or Melbourne?",
    "How does teamwork contribute to success in soccer?",
    "Why is water often called the universal solvent?",
    "How has Japan balanced tradition with modernity in its society?",
    "How does the Nile River impact the countries it flows through?",
    "Why was the discovery of penicillin a turning point in medicine?",
    "How has the speed of light shaped our understanding of physics?",
    "Why did France gift the Statue of Liberty to the United States?",
    "How has avocado become a staple in diets around the world?",
    "Why is the lotus flower considered significant in Indian culture?",
    "What makes Jupiter’s moon system so fascinating to scientists?",
    "How do astronomers study distant stars and galaxies?",
    "Why is the Sahara Desert both a challenge and a resource for nearby nations?",
    "How does nitrogen contribute to Earth’s atmosphere and ecosystems?",
    "Why is English often used as a global language of communication?",
    "How did Charles Babbage’s ideas influence modern computing?",
    "How is Diwali celebrated, and what does it symbolize?",
    "What role has Cairo played in Egypt’s history and development?",
    "Why is O-negative blood considered the universal donor type?",
    "How does the Fahrenheit scale differ from Celsius in practical use?",
    "What role has the British pound played in global finance?",
    "How has Homer’s 'Odyssey' influenced storytelling through history?",
    "Why are kidneys essential for maintaining a healthy body?",
    "How does Vatican City function as both a country and a religious center?",
    "Why is nitrogen the most abundant gas in Earth’s atmosphere?"
]

async def make_request(session: aiohttp.ClientSession, request_id: int, topic: str, model: str) -> Dict[str, Any]:
    """
    Make a single asynchronous HTTP request to the OpenAI-compatible API.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "assistant", "content": "I'm here to help!"},
            {"role": "user", "content": PROMPT_TEMPLATE.format(topic=topic)}
        ],
        "max_tokens": MAX_OUTPUT_TOKENS,
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

async def run_concurrent_requests(num_parallel_calls: int, num_requests: int, topics: List[str], model: str, request_offset: int = 0) -> List[Dict[str, Any]]:
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
    topics: List[str],
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
                topics,
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
            topics=TOPICS,
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
            TOPICS,
            args.model
        )
        analyze_results(results, total_time=time.time()-total_time)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
