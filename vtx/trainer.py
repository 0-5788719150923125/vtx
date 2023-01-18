from aitextgen.TokenDataset import TokenDataset, merge_datasets
from aitextgen.tokenizers import train_tokenizer
from aitextgen.utils import build_gpt2_config
from aitextgen import aitextgen
from transformers import GPT2Config, GPTNeoConfig
from pytorch_lightning import loggers
import numpy as np
import os
import shutil, tempfile

os.environ["TOKENIZERS_PARALLELISM"] = "true"

focus = os.environ["FOCUS"]
base_model = ""
vocab_path = "/lab/texts"
model_folder = "vtx/models/" + focus
tokenizer_file = "src." + focus + ".tokenizer.json"

vocab_size = 2048
max_length = 256
block_size = max_length
batch_size = 8

logger = loggers.TensorBoardLogger(
    "/lab/logs", name=focus, version=0, default_hp_metric=False
)
# logger.experiment.add_scalars(
#     "losses", {"train_loss": loss}, global_step=self.current_epoch
# )
# tmp = tempfile.mkdtemp()
# logger.log_hyperparams({"epochs": 1, "optimizer": "Adam"})
# logger.log_metrics({"acc": 0.75})
# logger.log_metrics({"acc": 0.9})
# logger.finalize("success")
# shutil.rmtree(tmp)


def list_full_paths(directory):
    fname = []
    for root, d_names, f_names in os.walk(directory):
        for f in f_names:
            fname.append(os.path.join(root, f))

    return fname


def create_token_dataset(path, line_by_line, block_size=None):
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
            print("something failed while tokenizing " + file)
    return datasets


if __name__ == "__main__":

    print("\033[91m" + "focus" + "\033[0m")
    print("\033[91m" + "ed on the " + focus + "\033[0m")

    if focus == "heart":
        base_model = "EleutherAI/gpt-neo-125M"
        block_size = 256
        batch_size = 8
        gradient_accumulation_steps = 6
        num_steps = 5000
        config = None
        to_gpu = True
        n_gpu = 1
        fp16 = False
        use_deepspeed = False
    elif focus == "soul":
        base_model = "xhyi/PT_GPTNEO350_ATG"
        vocab_size = 4096
        block_size = 256
        batch_size = 1
        gradient_accumulation_steps = 32
        num_steps = 5000
        config = None
        to_gpu = True
        n_gpu = 1
        fp16 = False
        use_deepspeed = False

    train_tokenizer(
        files=list_full_paths(vocab_path),
        vocab_size=vocab_size,
        save_path="./",
        prefix="src." + focus,
        dropout=0.0,
    )

    # research = create_token_dataset("/lab/research", False)
    journals = create_token_dataset("/lab/journals", False, block_size=block_size)
    pages = create_token_dataset("/lab/pages", False, block_size=block_size)
    texts = create_token_dataset("/lab/texts", False, block_size=block_size)

    flat_list = [item for sublist in [journals, pages, texts] for item in sublist]

    merged = merge_datasets(flat_list, equalize=False)

    ai = aitextgen(
        tokenizer_file=tokenizer_file,
        config=config,
        model=base_model,
        # model_folder=model_folder,
        to_gpu=to_gpu,
        gradient_checkpointing=True,
    )

    ai.train(
        merged,
        from_cache=False,
        batch_size=batch_size,
        num_steps=num_steps,
        generate_every=250,
        save_every=1000,
        n_gpu=n_gpu,
        output_dir=model_folder,
        tokenizer_file=tokenizer_file,
        loggers=logger,
        learning_rate=0.001,
        num_workers=8,
        max_grad_norm=1,
        use_deepspeed=use_deepspeed,
        gradient_accumulation_steps=gradient_accumulation_steps,
        fp16=fp16,
        # fp16_opt_level=fp16_opt_level,
    )
