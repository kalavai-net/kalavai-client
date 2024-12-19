import argparse
import json
import os
import pathlib


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--models-path", type=str)
    parser.add_argument("--model-extension", type=str, default="*.gguf")
    parser.add_argument("--separator", type=str, default=";")
    parser.add_argument("--output-filename", type=str, default="config.json")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)

    args = parser.parse_args()

    all_models = list(pathlib.Path(args.models_path).glob(args.model_extension))
    models = []
    for idx, model in enumerate(all_models):
        models.append({
            "model": os.path.join(args.models_path, model.name),
            "model_alias": model.name,
            #"chat_format": "chatml",
            # "n_gpu_layers": -1,
            # "n_threads": 12,
            # "n_batch": 512,
            # "n_ctx": 2048
        })

    config = {
        "host": args.host,
        "port": args.port,
        "models": models
    }
    print(json.dumps(config, indent=2))

    with open(args.output_filename, "w") as f:
        json.dump(config, f)
