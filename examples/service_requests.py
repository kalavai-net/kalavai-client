"""
pip install aiohttp
"""
import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any

# Configuration
API_URL = "https://api.cogenai.kalavai.net/v1/chat/completions"  # Replace with your OpenAI-compatible API URL
API_KEY = ""  # Replace with your actual API key
MODEL = "mistralai/Mistral-Nemo-Instruct-2407"  # Replace with your model name
NUM_PARALLEL_CALLS = 100  # Change this to adjust number of parallel requests
NUM_REQUESTS = 1  # Total number of requests to make
MAX_OUTPUT_TOKENS = 50
PROMPT_TEMPLATE = "Answer the following question: {topic}"
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
