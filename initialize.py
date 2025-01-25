from pathlib import Path
from style_bert_vits2.logging import logger
from huggingface_hub import hf_hub_download

def download_tts_model():
    additional_files = {
        "litagin/sbv2_koharune_ami": [
            "koharune-ami/config.json",
            "koharune-ami/style_vectors.npy",
            "koharune-ami/koharune-ami.safetensors",
        ],
        "litagin/sbv2_amitaro": [
            "amitaro/config.json",
            "amitaro/style_vectors.npy",
            "amitaro/amitaro.safetensors",
        ],
    }

    for repo_id, files in additional_files.items():
        for file in files:
            if not Path(f"model_assets/{file}").exists():
                logger.info(f"Downloading {file}")
                hf_hub_download(
                    repo_id,
                    file,
                    local_dir="model_assets",
                )

if __name__ == "__main__":
    download_tts_model()