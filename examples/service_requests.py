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

API_URL = "https://mistral-small-3-2-24b-instruct-5ee6d8-shadow-vllm.spaces.kalavai.net/v1/chat/completions" #"https://testme-default-litellm.spaces.kalavai.net/v1" #"https://api.cogenai.kalavai.net/v1" #"https://api.cogenai.kalavai.net/v1"  # Replace with your OpenAI-compatible API URL
API_KEY = ""  # Replace with your actual API key
DEFAULT_MODEL = "unsloth/Mistral-Small-3.2-24B-Instruct-2506-FP8" #"Hastagaras/Jamet-8B-L3-MK.V-Blackroot" #mistralai/Mistral-Nemo-Instruct-2407"  # Replace with your model name


NUM_PARALLEL_CALLS = 80  # Change this to adjust number of parallel requests
NUM_REQUESTS = 720  # Total number of requests to make
MAX_OUTPUT_TOKENS = 40
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
    "Why is nitrogen the most abundant gas in Earth’s atmosphere?",
    "What are the main characteristics of French society and daily life?",
    "Explain the impact of Einstein's relativity theory on contemporary physics.",
    "Discuss the scientific and economic significance of gold.",
    "What factors make Mars suitable for human colonization?",
    "Describe George Washington's role in establishing the United States.",
    "What ecological functions do whales perform in ocean environments?",
    "Compare the climatic and biological diversity across continents.",
    "Explain why mathematics is fundamental to all scientific disciplines.",
    "Analyze the cultural impact of Romeo and Juliet on modern storytelling.",
    "Describe the biological importance of photosynthesis for ecosystems.",
    "How did World War II reshape international relations?",
    "Explain the industrial and decorative applications of diamonds.",
    "What factors contribute to the Mona Lisa's global fame?",
    "Describe the physiological role of oxygen in human metabolism.",
    "What are the primary dangers of climbing Mount Everest?",
    "How does Japanese culture drive its economic success?",
    "Explain the Pacific Ocean's role in global commerce and climate systems.",
    "How did the Apollo 11 mission alter space exploration perspectives?",
    "What distinguishes cheetahs from other feline predators?",
    "Explain the relationship between altitude and water boiling point.",
    "Describe the heart's critical functions in human physiology.",
    "How has ice hockey become a symbol of Canadian identity?",
    "Analyze the telephone's impact on global communication networks.",
    "Explain why two is the first prime number mathematically.",
    "How has Mandarin Chinese influenced global cultural exchange?",
    "What historical factors led to Canberra becoming Australia's capital?",
    "Explain the importance of collaboration in competitive soccer.",
    "What chemical properties make water an effective solvent?",
    "How does Japan integrate ancient traditions with modern technology?",
    "Describe the Nile River's influence on African civilizations.",
    "How did penicillin revolutionize medical treatment?",
    "Explain the significance of light speed in physical theories.",
    "What motivated France to donate the Statue of Liberty?",
    "How did avocados become globally popular in cuisine?",
    "Explain the religious and cultural symbolism of the lotus.",
    "What scientific questions surround Jupiter's moon system?",
    "Describe methods astronomers use to observe distant celestial bodies.",
    "How does the Sahara Desert affect neighboring African nations?",
    "Explain nitrogen's role in atmospheric composition and biological cycles.",
    "What factors made English a global lingua franca?",
    "How did Charles Babbage's designs anticipate modern computers?",
    "Describe the traditions and meanings of Diwali celebrations.",
    "What is Cairo's historical significance in Egyptian civilization?",
    "Explain why O-negative blood can be donated universally.",
    "Compare Fahrenheit and Celsius temperature scales in practice.",
    "How has the British pound influenced international markets?",
    "Describe the Odyssey's impact on narrative traditions.",
    "What physiological functions do kidneys perform in humans?",
    "How does Vatican City operate as a sovereign religious state?",
    "Explain the atmospheric processes that maintain nitrogen abundance.",
    "What defines contemporary French cultural identity?",
    "How did relativity theory transform our understanding of space-time?",
    "Discuss gold's unique properties and their practical applications.",
    "What technical challenges must be overcome for Mars colonization?",
    "How did Washington's leadership define early American democracy?",
    "Why are whales crucial for ocean food chain stability?",
    "What creates the diverse climates across Earth's continents?",
    "How does mathematical reasoning underpin scientific methodology?",
    "What literary techniques made Romeo and Juliet influential?",
    "Why is photosynthesis fundamental to Earth's energy cycle?",
    "How did post-WWII geopolitical boundaries change?",
    "What makes diamonds valuable beyond jewelry applications?",
    "What artistic elements make the Mona Lisa iconic?",
    "How does oxygen enable cellular respiration in humans?",
    "What environmental hazards exist on Mount Everest?",
    "How do cultural values shape Japan's business practices?",
    "Why is the Pacific Ocean central to maritime trade?",
    "How did lunar missions inspire future space programs?",
    "What evolutionary adaptations make cheetahs exceptional hunters?",
    "Why does atmospheric pressure affect boiling points?",
    "How does the circulatory system depend on heart function?",
    "What cultural meanings does hockey hold for Canadians?",
    "How did telephones revolutionize personal and business communication?",
    "What mathematical definition establishes two as prime?",
    "How does Chinese writing influence cultural expression?",
    "What political compromise created Australia's capital location?",
    "Why is strategic coordination essential in soccer tactics?",
    "What molecular characteristics enable water's solvency?",
    "How does Japanese society preserve heritage amid modernization?",
    "How does the Nile support agriculture and civilization?",
    "Why was penicillin a breakthrough in infection treatment?",
    "How does light speed limit physical interactions?",
    "What diplomatic relationship facilitated the Statue of Liberty gift?",
    "How did global trade spread avocado consumption?",
    "What spiritual meanings does the lotus represent in Hinduism?",
    "Why do scientists study Jupiter's moons for astrobiology?",
    "What technologies enable observation of distant galaxies?",
    "How does the Sahara both challenge and benefit regional economies?",
    "What biochemical processes involve nitrogen in ecosystems?",
    "How did British colonialism spread English globally?",
    "What computational concepts did Babbage pioneer?",
    "What rituals and beliefs define Diwali celebrations?",
    "How has Cairo evolved as a political and cultural center?",
    "What genetic factors determine blood type compatibility?",
    "Which countries primarily use Fahrenheit temperature scales?",
    "How has the pound's value changed over history?",
    "What heroic qualities in Odysseus influenced later protagonists?",
    "How do kidneys filter blood and regulate blood pressure?",
    "What powers does the Pope have as Vatican City's head?",
    "What prevents nitrogen from being depleted from the atmosphere?",
    "How does the World Wide Web function as a global information system?",
    "What are the key principles of artificial intelligence and machine learning?",
    "How does blockchain technology ensure secure transactions?",
    "What makes quantum computing different from classical computing?",
    "How has social media changed human communication patterns?",
    "What technological advances enabled the smartphone revolution?",
    "How do electric vehicles compare to traditional combustion engines?",
    "What role does renewable energy play in combating climate change?",
    "How do nuclear power plants generate electricity?",
    "What functions do satellites perform in modern communications?",
    "How does GPS determine precise locations on Earth?",
    "What are the main applications of robotics in industry?",
    "How does 3D printing transform manufacturing processes?",
    "What distinguishes virtual reality from augmented reality?",
    "How do vaccines train the immune system to fight diseases?",
    "What role does DNA play in heredity and genetic traits?",
    "How has cancer treatment evolved over the past century?",
    "What factors contribute to mental health disorders?",
    "How do antibiotics combat bacterial infections?",
    "What are the major types of surgical procedures performed today?",
    "How do medical imaging technologies like MRI and CT scans work?",
    "What strategies improve public health in developing nations?",
    "How does nutrition affect human development and disease prevention?",
    "What are the biological functions of sleep in humans?",
    "How does regular exercise benefit cardiovascular health?",
    "What role do neurons play in transmitting information in the brain?",
    "How does the immune system distinguish self from non-self?",
    "What methods do epidemiologists use to track disease outbreaks?",
    "How does the greenhouse effect contribute to global warming?",
    "What factors are driving the loss of global biodiversity?",
    "How do different types of pollution affect human health?",
    "What causes ocean acidification and its impact on marine life?",
    "How does deforestation contribute to climate change?",
    "What are the most effective methods for recycling plastic waste?",
    "How do solar panels convert sunlight into electricity?",
    "What makes wind energy a viable alternative to fossil fuels?",
    "How do volcanic eruptions affect local and global climates?",
    "What drives the movement of tectonic plates?",
    "Why are coral reefs considered the rainforests of the sea?",
    "How do rainforests contribute to global oxygen production?",
    "What factors cause glaciers to form and recede?",
    "How do rivers shape landscapes over geological time?",
    "What adaptations allow plants and animals to survive in deserts?",
    "How do mountain ranges influence weather patterns?",
    "What were the key achievements of ancient Mesopotamian civilization?",
    "How did the Industrial Revolution transform society and economy?",
    "What were the main causes and consequences of the Cold War?",
    "How did the Renaissance transform European art and science?",
    "What made ancient Egypt one of history's most enduring civilizations?",
    "How did the Silk Road facilitate cultural and economic exchange?",
    "What factors led to the Great Depression of the 1930s?",
    "How did the American Civil War reshape the United States?",
    "What role did the Berlin Wall play in Cold War geopolitics?",
    "How do Greek myths reflect ancient Greek values and beliefs?",
    "What distinguishes poetry from other forms of literature?",
    "How has the Bible influenced Western literature and culture?",
    "What are the core teachings of the Quran in Islam?",
    "How do fables convey moral lessons to readers?",
    "What elements define the novel as a literary form?",
    "How do fairy tales reflect cultural values across societies?",
    "What makes the periodic table fundamental to chemistry?",
    "How do chemical bonds determine molecular properties?",
    "What are the states of matter and how do they transition?",
    "How does the law of conservation of energy apply in physical systems?",
    "What causes earthquakes and how are they measured?",
    "How do magnets generate magnetic fields?",
    "What principles govern fluid dynamics in engineering?",
    "How does thermodynamics explain heat and energy transfer?",
    "What are the fundamental particles in atomic physics?",
    "How do lenses focus light in optical systems?",
    "What causes sound waves and how do they travel?",
    "How do semiconductors enable modern electronics?",
    "What makes graphene unique among materials?",
    "How do superconductors work at low temperatures?",
    "What are the main branches of philosophy and their key questions?",
    "How does ethical reasoning guide moral decision-making?",
    "What distinguishes deductive from inductive reasoning?",
    "How do different political systems distribute power?",
    "What are the core principles of democratic governance?",
    "How do international laws regulate relations between nations?",
    "What factors influence voter behavior in elections?",
    "How do economic systems like capitalism and socialism differ?",
    "What role does central banking play in modern economies?",
    "How do supply and demand determine market prices?",
    "What causes inflation and how does it affect consumers?",
    "How do taxes fund public services and infrastructure?",
    "What are the main components of gross domestic product?",
    "How does international trade benefit participating countries?",
    "What factors contribute to economic growth and development?",
    "How do stock markets function in allocating capital?",
    "What distinguishes microeconomics from macroeconomics?",
    "How do interest rates affect borrowing and saving?",
    "What causes economic recessions and recoveries?",
    "How do entrepreneurs drive innovation in markets?",
    "What role does consumer confidence play in economic stability?",
    "How do exchange rates affect international business?",
    "What are the main types of financial instruments?",
    "How does insurance manage risk in modern economies?"
]

async def make_request(session: aiohttp.ClientSession, request_id: int, topic: str, model: str) -> Dict[str, Any]:
    """
    Make a single asynchronous HTTP request to the OpenAI-compatible API.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": PROMPT_TEMPLATE.format(topic=topic)}
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
