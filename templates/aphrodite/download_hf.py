import argparse

from huggingface_hub import hf_hub_download


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--repo_id", type=str)
    parser.add_argument("--filename", type=str)
    parser.add_argument("--local_dir", type=str)

    args = parser.parse_args()
    downloaded_model_path = hf_hub_download(
        repo_id=args.repo_id,
        filename=args.filename,
        local_dir=args.local_dir,
        cache_dir=args.local_dir
    )

    print(f"[DOWNLOAD_HF] Downloaded: {downloaded_model_path}")


