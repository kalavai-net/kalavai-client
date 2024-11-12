import argparse
from pathlib import Path

from huggingface_hub import (
    hf_hub_download,
    snapshot_download
)


def download_repo(repo_id, local_dir=None):
    return snapshot_download(
        repo_id=repo_id,
        local_dir=local_dir,
        cache_dir=local_dir)

def download_model_file(repo_id, filename, local_dir=None):
    return hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=local_dir,
        cache_dir=local_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--repo_id", type=str)
    parser.add_argument("--filename", type=str, default=None)
    parser.add_argument("--local_dir", type=str)

    args = parser.parse_args()

    Path(args.local_dir).mkdir(parents=True, exist_ok=True)

    if args.filename is not None:
        downloaded_model_path = download_model_file(
            repo_id=args.repo_id,
            filename=args.filename,
            local_dir=args.local_dir
        )
    else:
        downloaded_model_path = download_repo(
            repo_id=args.repo_id,
            local_dir=args.local_dir
        )

    print(f"[DOWNLOAD_HF] Downloaded: {downloaded_model_path}")


