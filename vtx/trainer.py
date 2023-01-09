from aitextgen.TokenDataset import TokenDataset, merge_datasets
from aitextgen.tokenizers import train_tokenizer
from aitextgen.utils import build_gpt2_config
from aitextgen import aitextgen
from transformers import GPT2Config, GPTNeoConfig
import numpy as np
import os

os.environ["TOKENIZERS_PARALLELISM"] = "true"
os.environ["TRANSFORMERS_CACHE"] = "/tmp"

focus = os.environ["FOCUS"]
base_model = ""
corpus = "input.txt"
vocab_path = "/lab/research"
model_folder = "vtx/models/" + focus
tokenizer_file = "src." + focus + ".tokenizer.json"

vocab_size = 2048
max_length = 256
block_size = max_length
batch_size = 8


def list_full_paths(directory):
    return [os.path.join(directory, file) for file in os.listdir(directory)]


if __name__ == "__main__":

    train_tokenizer(
        files=list_full_paths(vocab_path),
        vocab_size=vocab_size,
        save_path="./",
        prefix="src." + focus,
        dropout=0.0,
    )

    if focus == "heart":
        base_model = "gpt2"
        config = build_gpt2_config(
            vocab_size=vocab_size,
            tokenizer_file=tokenizer_file,
            max_length=max_length,
            dropout=0.00000666,
            n_embd=888,
            n_layer=12,
            n_head=24,
            reorder_and_upcast_attn=True,
            scale_attn_by_inverse_layer_idx=True,
        )
    elif focus == "head":
        base_model = "EleutherAI/gpt-neo-125M"
        config = None
        block_size = 512
        batch_size = 4
        # config = GPTNeoConfig(
        #     vocab_size=50257,
        #     tokenizer_file=tokenizer_file,
        #     activation_function="gelu_new",
        #     attention_types=[[["global", "local"], 6]],
        #     hidden_size=512,
        #     window_size=256,
        #     intermediate_size=2048,
        #     num_layers=12,
        #     num_heads=16,
        #     embed_dropout=0.00000666,
        #     attention_dropout=0.00000666,
        #     resid_dropout=0.00000666,
        # )

    print("\033[91m" + "focus" + "\033[0m")
    print("\033[91m" + "ed on the " + focus + "\033[0m")

    ai = aitextgen(
        tokenizer_file=tokenizer_file,
        config=config,
        model=base_model,
        to_gpu=True,
        gradient_checkpointing=True,
    )

    data = TokenDataset(
        corpus, tokenizer_file=tokenizer_file, block_size=block_size, line_by_line=True
    )

    ai.train(
        data,
        from_cache=False,
        batch_size=batch_size,
        num_steps=100000,
        generate_every=250,
        save_every=1000,
        n_gpu=1,
        output_dir=model_folder,
        tokenizer_file=tokenizer_file,
    )
