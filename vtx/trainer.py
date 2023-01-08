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
model_folder = "vtx/models/" + focus
tokenizer_file = "src.tokenizer.json"

vocab_size = 3333
max_length = 256


def list_full_paths(directory):
    return [os.path.join(directory, file) for file in os.listdir(directory)]


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


if __name__ == "__main__":

    train_tokenizer(
        files=list_full_paths("/lab/research"),
        vocab_size=vocab_size,
        save_path="./",
        prefix="src",
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
        config = GPTNeoConfig(
            vocab_size=vocab_size,
            tokenizer_file=tokenizer_file,
            activation_function="gelu_new",
            attention_types=[[["global", "local"], 6]],
            hidden_size=512,
            window_size=256,
            intermediate_size=2048,
            num_layers=12,
            num_heads=16,
            embed_dropout=0.00000666,
            attention_dropout=0.00000666,
            resid_dropout=0.00000666,
        )

    print(bcolors.FAIL + "focus" + bcolors.ENDC)
    print(bcolors.FAIL + "ed on the " + focus + bcolors.ENDC)

    ai = aitextgen(
        tokenizer_file=tokenizer_file,
        # config=config,
        model=base_model,
        to_gpu=True,
        gradient_checkpointing=True,
    )

    data = TokenDataset(corpus, tokenizer_file=tokenizer_file, block_size=max_length)

    ai.train(
        data,
        line_by_line=False,
        from_cache=False,
        batch_size=8,
        num_steps=100000,
        generate_every=250,
        save_every=1000,
        n_gpu=1,
        output_dir=model_folder,
        tokenizer_file=tokenizer_file,
    )
