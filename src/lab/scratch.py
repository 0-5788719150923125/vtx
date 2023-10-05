# from lab.aigen.aigen.TokenDataset import TokenDataset
# from transformers import AutoTokenizer
# from datasets import load_dataset, load_from_disk

# https://huggingface.co/docs/transformers/model_doc/rwkv
# import time

# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer, RwkvConfig, RwkvModel

# model_name = "RWKV/rwkv-4-430m-pile"

# string = "Once upon a time,"


# tokenizer = AutoTokenizer.from_pretrained(
#     model_name,
#     cache_dir="/src/models",
# )
# model = AutoModelForCausalLM.from_pretrained(
#     model_name,
#     cache_dir="/src/models",
#     output_hidden_states=True,
#     device_map="auto",
#     torch_dtype=torch.bfloat16,
# )

# state = None

# with torch.no_grad():
#     while True:
#         inputs = tokenizer(string, return_tensors="pt")
#         outputs = model(inputs["input_ids"].to(model.device.type), state=state)
#         state = outputs.state
#         string = tokenizer.decode(
#             model.generate(
#                 inputs["input_ids"].to(model.device.type),
#                 max_new_tokens=3,
#                 do_sample=True,
#                 temperature=1.23,
#                 top_k=4,
#                 penalty_alpha=0.6,
#                 eta_cutoff=0.0003,
#                 repetition_penalty=2.3,
#                 no_repeat_ngram_size=9,
#                 state=state,
#             )[0]
#         )
#         while len(string) > 1024:
#             string = string[1:]
#         print("------------------")
#         print(string)
#         time.sleep(1)

# # model_name = "EleutherAI/pythia-1b-deduped"

# # model = RwkvModel.from_pretrained(model_name, cache_dir="/src/models")

# inputs = tokenizer(string, return_tensors="pt")
# # # Feed everything to the model
# outputs = model(inputs["input_ids"])
# # print(outputs)
# output_whole = outputs.hidden_states[-1]
# print(output_whole)

# outputs = model(inputs["input_ids"][:, :2])
# print(outputs.hidden_states[-1])


# from transformers import AutoTokenizer, RwkvConfig, RwkvModel

# model_name = "RWKV/rwkv-4-169m-pile"

# model = AutoModelForCausalLM.from_pretrained(
#     model_name, cache_dir="/src/models", output_hidden_states=True
# )
# tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir="/src/models")

# inputs = tokenizer("This is an example.", return_tensors="pt")
# # Feed everything to the model
# outputs = model(inputs["input_ids"])
# output_whole = outputs.hidden_states[-1]

# print(output_whole)

# outputs1 = model.generate(
#     inputs["input_ids"],
#     state=outputs.state,
#     output_hidden_states=True,
#     return_dict_in_generate=True,
# )
# print(outputs1["hidden_states"][0][-1][-1])

# outputs2 = model.generate(
#     inputs["input_ids"],
#     state=outputs1["hidden_states"][0],
#     output_hidden_states=True,
#     return_dict_in_generate=True,
# )

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
# print(tokenizer.decode(outputs[0], skip_special_tokens=True))
# print(tokenizer.decode(outputs[0], skip_special_tokens=True))
# print(tokenizer.decode(outputs[0], skip_special_tokens=True))
