from aitextgen.TokenDataset import TokenDataset, merge_datasets
from aitextgen.tokenizers import train_tokenizer
from aitextgen.utils import build_gpt2_config
from aitextgen import aitextgen
from transformers import GPT2Config, GPTNeoConfig
from pytorch_lightning.loggers import CSVLogger
import numpy as np
import os

os.environ["TOKENIZERS_PARALLELISM"] = "true"
os.environ["TRANSFORMERS_CACHE"] = "/tmp"

focus = os.environ["FOCUS"]
base_model = ""
vocab_path = "/lab/texts"
model_folder = "vtx/models/" + focus
tokenizer_file = "src." + focus + ".tokenizer.json"

vocab_size = 2048
max_length = 256
block_size = max_length
batch_size = 8

logger = CSVLogger("/lab/logs", name=focus)


def list_full_paths(directory):
    fname = []
    for root, d_names, f_names in os.walk(directory):
        for f in f_names:
            fname.append(os.path.join(root, f))

    return fname


def create_token_dataset(path, line_by_line):
    files = list_full_paths(path)
    datasets = []
    for file in files:
        try:
            datasets.append(
                TokenDataset(
                    file,
                    tokenizer_file=tokenizer_file,
                    block_size=block_size,
                    line_by_line=line_by_line,
                )
            )
        except:
            print("something failed in " + file)
    return datasets


if __name__ == "__main__":

    train_tokenizer(
        files=list_full_paths(vocab_path),
        vocab_size=vocab_size,
        save_path="./",
        prefix="src." + focus,
        dropout=0.0666,
    )

    research = create_token_dataset("/lab/research", False)
    journals = create_token_dataset("/lab/journals", False)
    pages = create_token_dataset("/lab/pages", False)
    texts = create_token_dataset("/lab/texts", False)

    flat_list = [
        item for sublist in [research, journals, pages, texts] for item in sublist
    ]

    merged = merge_datasets(flat_list, equalize=False)

    print("\033[91m" + "focus" + "\033[0m")
    print("\033[91m" + "ed on the " + focus + "\033[0m")

    if focus == "heart":
        base_model = "gpt2"
        config = build_gpt2_config(
            vocab_size=vocab_size,
            tokenizer_file=tokenizer_file,
            max_length=max_length,
            dropout=0.0666,
            n_embd=1024,
            n_layer=12,
            n_head=16,
            reorder_and_upcast_attn=True,
            scale_attn_by_inverse_layer_idx=True,
        )
    elif focus == "head":
        base_model = "EleutherAI/gpt-neo-125M"
        block_size = 512
        batch_size = 4
        config = None
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

    ai = aitextgen(
        tokenizer_file=tokenizer_file,
        config=config,
        model=base_model,
        to_gpu=True,
        gradient_checkpointing=True,
    )

    ai.train(
        merged,
        from_cache=False,
        batch_size=batch_size,
        num_steps=100000,
        generate_every=250,
        save_every=1000,
        n_gpu=1,
        output_dir=model_folder,
        tokenizer_file=tokenizer_file,
        loggers=logger,
        learning_rate=0.001,
        num_workers=8,
        max_grad_norm=1,
    )
