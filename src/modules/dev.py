import os
import time

if os.environ.get("DEV_MODE", "false") == "true":
    import debugpy

    time.sleep(1)
    debugpy.listen(("0.0.0.0", 5678))

# ------ OPT ----------
# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# model = AutoModelForCausalLM.from_pretrained(
#     "HuggingFaceTB/SmolLM-360M-Instruct",
#     cache_dir="/data/models",
#     trust_remote_code=True,
#     device_map="cpu",
# )
# tokenizer = AutoTokenizer.from_pretrained(
#     "HuggingFaceTB/SmolLM-360M-Instruct",
#     cache_dir="/data/models",
#     trust_remote_code=True,
# )

# prompt = "Once upon a time,"

# print("starting generation")
# inputs = tokenizer(prompt, return_tensors="pt")
# output = model.generate(
#     inputs["input_ids"], max_new_tokens=32, do_sample=True, temperature=0.7
# )
# print(tokenizer.decode(output[0].tolist(), skip_special_tokens=False))


# ----- Mamba ------ #
# from transformers import MambaConfig, MambaForCausalLM, AutoTokenizer
# import torch

# tokenizer = AutoTokenizer.from_pretrained("state-spaces/mamba-130m-hf")
# model = MambaForCausalLM.from_pretrained("state-spaces/mamba-130m-hf")
# input_ids = tokenizer("Hey how are you doing?", return_tensors="pt")["input_ids"]

# out = model.generate(input_ids, max_new_tokens=10)
# print(tokenizer.batch_decode(out))

# ----- RWKV v5 ------ #
# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer

# model = AutoModelForCausalLM.from_pretrained(
#     "RWKV/rwkv-5-world-1b5", cache_dir="/data/models", trust_remote_code=True
# ).to(torch.float32)
# tokenizer = AutoTokenizer.from_pretrained(
#     "RWKV/rwkv-5-world-1b5", cache_dir="/data/models", trust_remote_code=True
# )

# prompt = "Once upon a time,"

# inputs = tokenizer(prompt, return_tensors="pt")
# output = model.generate(
#     inputs["input_ids"],
#     max_new_tokens=333,
#     do_sample=True,
#     temperature=1.0,
#     top_p=0.3,
#     top_k=0,
# )
# print(tokenizer.decode(output[0].tolist(), skip_special_tokens=True))


# ------ Q Training ------------ #

# import time

# import torch
# from transformers import (
#     AutoModelForCausalLM,
#     AutoTokenizer,
# )

# model_name = "cerebras/Cerebras-GPT-111M"

# tokenizer = AutoTokenizer.from_pretrained(
#     model_name, cache_dir="/data/models"
# )
# model = AutoModelForCausalLM.from_pretrained(
#     model_name,
#     cache_dir="/data/models",
#     output_hidden_states=True,
#     device_map="auto",
#     torch_dtype=torch.bfloat16,
#     load_in_4bit=True,
#     bnb_4bit_quant_type="nf4",
#     bnb_4bit_use_double_quant=True,
#     bnb_4bit_compute_dtype=True
# )

# peft_config = IA3Config(
#     task_type="CAUSAL_LM",
#     target_modules=p.get("target_modules", None),
#     feedforward_modules=p.get("feedforward_modules", None),
# )

# ------ Iterable Datasets ------- #

# import random

# import datasets

# datasets.logging.set_verbosity_info()

# dataset = datasets.load_dataset(
#     "HuggingFaceTB/cosmopedia",
#     name="web_samples_v2",
#     # snapshots=["2023-14"],
#     # languages=["en"],
#     # split="validation",
#     streaming=True,
#     cache_dir="/data/pile",
# ).shuffle(seed=random.randint(0, 9), buffer_size=10)

# # print(next(iter(dataset["train"])))
# small_ds = dataset["train"].take(1)
# thing = next(iter(small_ds))
# print(thing.get("prompt"))

# ------- ModuleFormers --------#

# import torch
# from moduleformer import (
#     ModuleFormerConfig,
#     ModuleFormerForCausalLM,
#     ModuleFormerForSequenceClassification,
# )
# from transformers import (
#     AutoConfig,
#     AutoModelForCausalLM,
#     AutoModelForSequenceClassification,
#     AutoTokenizer,
# )

# AutoConfig.register("moduleformer", ModuleFormerConfig)
# AutoModelForCausalLM.register(ModuleFormerConfig, ModuleFormerForCausalLM)
# AutoModelForSequenceClassification.register(
#     ModuleFormerConfig, ModuleFormerForSequenceClassification
# )

# model_name = "ibm/MoLM-350M-4B"

# tokenizer = AutoTokenizer.from_pretrained(
#     model_name, cache_dir="/data/models", padding_side="left"
# )

# model = AutoModelForCausalLM.from_pretrained(
#     model_name,
#     cache_dir="/data/models",
#     output_hidden_states=True,
#     device_map="auto",
#     torch_dtype=torch.bfloat16,
#     load_in_4bit=True,
#     bnb_4bit_quant_type="nf4",
#     bnb_4bit_use_double_quant=True,
#     bnb_4bit_compute_dtype=torch.bfloat16,
# )

# string = "Once upon a time,"

# inputs = tokenizer(string, return_tensors="pt")
# generated = model.generate(
#     input_ids=inputs["input_ids"].to(model.device.type),
#     attention_mask=inputs["attention_mask"].to(model.device.type),
#     max_new_tokens=33,
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


# ------- Ray ------- #
# import time

# import ray
# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer


# @ray.remote
# def generate():
#     model_name = "EleutherAI/pythia-410m-deduped"

#     tokenizer = AutoTokenizer.from_pretrained(
#         model_name, cache_dir="/data/models", padding_side="left"
#     )
#     model = AutoModelForCausalLM.from_pretrained(
#         model_name,
#         cache_dir="/data/models",
#         output_hidden_states=True,
#         device_map="cpu",
#         torch_dtype=torch.bfloat16,
#     )
#     generated = model.generate(
#         max_new_tokens=333,
#         do_sample=True,
#         temperature=0.7,
#         top_k=4,
#         penalty_alpha=0.6,
#         eta_cutoff=0.0003,
#         repetition_penalty=2.3,
#         no_repeat_ngram_size=9,
#         output_hidden_states=True,
#         return_dict_in_generate=True,
#     )
#     return tokenizer.decode(generated["sequences"][0], skip_special_tokens=False)


# ray.init(num_cpus=4)

# # Call the generate() function
# start_time = time.time()
# generated_text = ray.get(generate.remote())
# # generated_text = generate()
# end_time = time.time()

# execution_time = end_time - start_time
# print(f"Execution time: {execution_time} seconds")

# # Shutdown Ray
# # ray.shutdown()

# # Print the generated text
# print(generated_text)

# # ------ ViT ------- #

# import requests
# from PIL import Image
# from transformers import AutoFeatureExtractor, ViTForImageClassification

# # url = "http://images.cocodataset.org/val2017/000000039769.jpg"
# # image = Image.open(requests.get(url, stream=True).raw)
# image = Image.open("/data/meme.webp")
# feature_extractor = AutoFeatureExtractor.from_pretrained(
#     "facebook/deit-tiny-patch16-224"
# )
# model = ViTForImageClassification.from_pretrained("facebook/deit-tiny-patch16-224")
# inputs = feature_extractor(images=image, return_tensors="pt")
# outputs = model(**inputs)
# logits = outputs.logits
# # model predicts one of the 1000 ImageNet classes
# predicted_class_idx = logits.argmax(-1).item()
# print("Predicted class:", model.config.id2label[predicted_class_idx])

# from transformers import AutoTokenizer

# tokenizer = AutoTokenizer.from_pretrained("RWKV/rwkv-4-169m-pile")

# tokenized_texts = tokenizer("this is a test", return_tensors="pt")


# import lightning as L
# from torch.utils.data import Dataset


# class TextDataset(Dataset):
#     def __init__(self, tokenized_texts):
#         self.tokenized_texts = tokenized_texts

#     def __len__(self):
#         return len(self.tokenized_texts)

#     def __getitem__(self, idx):
#         return self.tokenized_texts[idx]


# # Create the Lightning AI Dataset.
# dataset = TextDataset(tokenized_texts)

# print(len(dataset))

# ------ Local Agents -------- #

# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer, LocalAgent

# checkpoint = "bigcode/starcoder"
# model = AutoModelForCausalLM.from_pretrained(
#     checkpoint, device_map="auto", torch_dtype=torch.bfloat16
# )
# tokenizer = AutoTokenizer.from_pretrained(checkpoint)

# agent = LocalAgent(model, tokenizer)
# agent.run("Draw me a picture of rivers and lakes.")

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
# from transformers import (
#     AutoModelForCausalLM,
#     AutoTokenizer,
#     RwkvConfig,
#     RwkvForCausalLM,
#     RwkvModel,
# )

# model_name = "EleutherAI/gpt-neo-125M"

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
