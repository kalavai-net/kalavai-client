# Distributed llama.cpp 

https://github.com/ggerganov/llama.cpp/tree/master/examples/rpc

To support GPU, worker image must be built against adequate drivers.



Full list of parameters: https://github.com/ggerganov/llama.cpp/tree/master/examples/server
- -np X (concurrent requests)


curl http://0.0.0.0:8080/completions \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "I would walk 500",
        "max_tokens": 100,
        "temperature": 0.2
    }'


LocalAI
- https://localai.io/features/distribute/