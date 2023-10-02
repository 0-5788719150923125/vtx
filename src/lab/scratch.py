# from lab.aigen.aigen.TokenDataset import TokenDataset
# from transformers import AutoTokenizer
# from datasets import load_dataset, load_from_disk

# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer, RwkvConfig, RwkvModel

# # model_name = "EleutherAI/pythia-1b-deduped"
# model_name = "RWKV/rwkv-4-169m-pile"

# string = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."

# https://huggingface.co/docs/transformers/model_doc/rwkv
# This stuff was used to use RWKV in RNN mode
# tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir="/src/models")
# model = AutoModelForCausalLM.from_pretrained(
#     model_name, cache_dir="/src/models", output_hidden_states=True
# )
# # model = RwkvModel.from_pretrained(model_name, cache_dir="/src/models")

# inputs = tokenizer(string, return_tensors="pt")
# # # Feed everything to the model
# outputs = model(inputs["input_ids"])
# # print(outputs)
# output_whole = outputs.hidden_states[-1]
# print(output_whole)

# outputs = model(inputs["input_ids"][:, :2])
# print(outputs.hidden_states[-1])


# my_dataset = load_dataset(
#     "text", data_files="/lab/ink/content/docs/black.md", split="train"
# )

# print(my_dataset["text"])

# string = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."

# print(
#     TokenDataset(
#         "/book/content/pillars.md",
#         tokenizer=tokenizer,
#         block_size=32,
#         padding_side="left",
#     )
# )
# print(
#     NewTokenDataset(
#         "/lab/juxtaposition/2/fibonacci.csv",
#         # "/book/content/pillars.md",
#         tokenizer=tokenizer,
#         block_size=32,
#         stride=4,
#         padding_side="left",
#     )
# )

# print(string)

# tokenizer.pad_token = tokenizer.eos_token

# inputs = tokenizer(
#     string,
#     max_length=16,
#     padding=True,
#     truncation=True,
#     stride=4,
#     return_overflowing_tokens=True,
# )

# print(inputs)

# inputs = inputs.convert_to_tensors("pt")

# print(inputs)

# inputs = tokenizer("Harry Potter is", return_tensors="pt")["input_ids"]
# inputs = None

# outputs = model.generate(
#     inputs=inputs,
#     do_sample=True,
#     temperature=0.7,
#     eta_cutoff=0.0003,
#     penalty_alpha=0.6,
#     top_k=4,
#     repetition_penalty=2.3,
#     no_repeat_ngram_size=9,
#     max_new_tokens=222,
# )
# print(tokenizer.decode(outputs[0], skip_special_tokens=True))
