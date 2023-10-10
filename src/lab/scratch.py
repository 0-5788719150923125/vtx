# ------ Retrieval Augmented Generation -------#

# from transformers import RagRetriever, RagTokenForGeneration, RagTokenizer

# tokenizer = RagTokenizer.from_pretrained(
#     "facebook/rag-token-nq", cache_dir="/data/models"
# )
# retriever = RagRetriever.from_pretrained(
#     "facebook/rag-token-nq",
#     cache_dir="/data/models",
#     index_name="exact",
#     use_dummy_dataset=True,
# )
# model = RagTokenForGeneration.from_pretrained(
#     "facebook/rag-token-nq",
#     retriever=retriever,
#     cache_dir="/data/models",
# )

# input_dict = tokenizer.prepare_seq2seq_batch(
#     "what is the sum of 2+2?", return_tensors="pt"
# )

# generated = model.generate(input_ids=input_dict["input_ids"], max_new_tokens=66)
# print(tokenizer.batch_decode(generated, skip_special_tokens=True)[0])


# from lab.aigen.aigen.TokenDataset import TokenDataset
# from transformers import AutoTokenizer
# from datasets import load_dataset, load_from_disk


# ------- inference ------- #
# import time

# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer

# model_name = "EleutherAI/pythia-410m-deduped"

# tokenizer = AutoTokenizer.from_pretrained(
#     model_name, cache_dir="/data/models", padding_side="left"
# )
# model = AutoModelForCausalLM.from_pretrained(
#     model_name,
#     cache_dir="/data/models",
#     output_hidden_states=True,
#     device_map="auto",
#     torch_dtype=torch.bfloat16,
# )

# string = "Once upon a time,"

# inputs = tokenizer(string, return_tensors="pt")
# generated = model.generate(
#     inputs["input_ids"].to(model.device.type),
#     max_new_tokens=333,
#     do_sample=True,
#     temperature=0.7,
#     top_k=4,
#     penalty_alpha=0.6,
#     eta_cutoff=0.0003,
#     repetition_penalty=2.3,
#     no_repeat_ngram_size=9,
#     output_hidden_states=True,
#     return_dict_in_generate=True,
# )
# string = tokenizer.decode(generated["sequences"][0], skip_special_tokens=False)
# print(string)


# https://huggingface.co/docs/transformers/model_doc/rwkv
# import time

# import torch
# from transformers import (
#     AutoModelForCausalLM,
#     AutoTokenizer,
#     RwkvConfig,
#     RwkvForCausalLM,
#     RwkvModel,
# )

# model_name = "RWKV/rwkv-4-430m-pile"

# tokenizer = AutoTokenizer.from_pretrained(
#     model_name, cache_dir="/data/models", padding_side="left"
# )
# model = AutoModelForCausalLM.from_pretrained(
#     model_name,
#     cache_dir="/data/models",
#     output_hidden_states=True,
#     device_map="auto",
#     torch_dtype=torch.bfloat16,
# )

# string = "Once upon a time,"
# complete = string

# with torch.no_grad():
#     state = None

#     while True:
#         inputs = tokenizer(string, return_tensors="pt")
#         outputs = model(inputs["input_ids"].to(model.device.type), state=state)
#         state = outputs.state
#         generated = model.generate(
#             # inputs["input_ids"].to(model.device.type),
#             max_new_tokens=3,
#             do_sample=True,
#             temperature=0.7,
#             top_k=4,
#             penalty_alpha=0.6,
#             eta_cutoff=0.0003,
#             repetition_penalty=2.3,
#             no_repeat_ngram_size=9,
#             output_hidden_states=True,
#             return_dict_in_generate=True,
#             state=state,
#         )
#         # state = generated["hidden_states"][0][:-1]
#         string = tokenizer.decode(generated["sequences"][0])
#         # complete = result
#         # string = result.lstrip(string)
#         # while len(string) > 1024:
#         #     string = string[1:]
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
# print(tokenizer.decode(outputs[0], skip_special_tokens=True))
