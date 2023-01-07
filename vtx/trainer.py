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
research = "/lab/research/2eng_hebrew.txt"
model_folder = "vtx/models/" + focus
tokenizer_file = "tokens.json"
merges_file = "merges.json"
vocab_file = "vocab.json"

vocab_size = 2048
max_length = 256


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
    train_tokenizer(research, vocab_size=vocab_size, save_path=tokenizer_file)
    train_tokenizer(corpus, vocab_size=vocab_size, save_path=tokenizer_file)

    if focus == "heart":
        base_model = "gpt2"
        config = build_gpt2_config(
            vocab_size=vocab_size,
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
            vocab_size=50257,
            tokenizer_file=tokenizer_file,
            activation_function="gelu_new",
            attention_types=[[["global", "local"], 6]],
            hidden_size=768,
            window_size=256,
            intermediate_size=2048,
            num_layers=12,
            num_heads=24,
            embed_dropout=0.00000666,
            attention_dropout=0.00000666,
            resid_dropout=0.00000666,
        )

    print(bcolors.FAIL + "focus" + bcolors.ENDC)
    print(bcolors.FAIL + "ed on the " + focus + bcolors.ENDC)

    ai = aitextgen(
        tokenizer_file=tokenizer_file,
        vocab_file=tokenizer_file,
        merges_file=tokenizer_file,
        config=config,
        model=base_model,
        to_gpu=True,
        gradient_checkpointing=True,
    )

    data1 = TokenDataset(
        research,
        tokenizer_file=tokenizer_file,
        vocab_file=tokenizer_file,
        merges_file=tokenizer_file,
        block_size=max_length,
    )

    data2 = TokenDataset(
        corpus,
        tokenizer_file=tokenizer_file,
        vocab_file=tokenizer_file,
        merges_file=tokenizer_file,
        block_size=max_length,
        # save_cache=True,
        # from_cache=True,
        # cache_destination="dataset_cache.tar.gz",
    )

    # data_merged = merge_datasets([np.asarray(data1), np.asarray(data2)])

    print("data failed to merge")

    ai.train(
        data2,
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
