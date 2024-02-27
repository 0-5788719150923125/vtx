import sys

import lm_eval

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".", "aigen"))
)

try:
    from aigen.aigen import aigen
    from aigen.aigen.datasets import StaticDataset, merge_datasets
    from aigen.aigen.tokenizers import train_tokenizer
    from aigen.aigen.tuners import optimize_hparams
except:
    from aigen import aigen
    from aigen.datasets import StaticDataset, merge_datasets
    from aigen.tokenizers import train_tokenizer
    from aigen.tuners import optimize_hparams


# import lm_eval

# MODEL = "/data/models/src"  # Replace with your model path

# args = {
#     "model": "hf",
#     "model_args": {
#         "pretrained": MODEL,
#         "cache_dir": "/data/models",
#         "trust_remote_code": True
#     },
#     "tasks": ["arc_easy", "arc_challenge", "hellaswag", "openbookqa", "piqa"],
#     "device": "cuda:1",
#     "batch_size": "auto"
# }

# lm_eval.main(args)


# Apparently, this is the supported method:
# https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/interface.md


# ...

# my_model = initialize_my_model() # create your model (could be running finetuning with some custom modeling code)
# ...
# # instantiate an LM subclass that takes your initialized model and can run
# # - `Your_LM.loglikelihood()`
# # - `Your_LM.loglikelihood_rolling()`
# # - `Your_LM.generate_until()`
# lm_obj = Your_LM(model=my_model, batch_size=16)

# # indexes all tasks from the `lm_eval/tasks` subdirectory.
# # Alternatively, you can set `TaskManager(include_path="path/to/my/custom/task/configs")`
# # to include a set of tasks in a separate directory.
# task_manager = lm_eval.tasks.TaskManager()

# # Setting `task_manager` to the one above is optional and should generally be done
# # if you want to include tasks from paths other than ones in `lm_eval/tasks`.
# # `simple_evaluate` will instantiate its own task_manager is the it is set to None here.
# results = lm_eval.simple_evaluate( # call simple_evaluate
#     model=lm_obj,
#     tasks=["taskname1", "taskname2"],
#     num_fewshot=0,
#     task_manager=task_manager,
#     ...
# )
