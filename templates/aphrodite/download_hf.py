import argparse

from huggingface_hub import (
    hf_hub_download,
    snapshot_download
)

CACHE_DIR = "/dev/shm"


def download_repo(repo_id, local_dir=None):
    return snapshot_download(
        repo_id=repo_id,
        local_dir=local_dir,
        cache_dir=CACHE_DIR)

def download_model_file(repo_id, filename, local_dir=None):
    return hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=local_dir,
        cache_dir=CACHE_DIR)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--repo_id", type=str)
    parser.add_argument("--filename", type=str, default=None)
    parser.add_argument("--local_dir", type=str)

    args = parser.parse_args()

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


