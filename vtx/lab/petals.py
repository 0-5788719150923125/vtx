import torch
from transformers import AutoTokenizer
from petals import AutoDistributedModelForCausalLM


async def orchestrate(config):
    print('trying petals')
    try:
        model = AutoDistributedModelForCausalLM.from_pretrained("bigscience/bloomz", cache_dir="models", torch_dtype=torch.float32)
        tokenizer = AutoTokenizer.from_pretrained("bigscience/bloomz", cache_dir="models")
        inputs = tokenizer("A cat sat", return_tensors="pt")["input_ids"]
        outputs = model.generate(inputs, max_new_tokens=5)
        print(tokenizer.decode(outputs[0]))  # A cat sat on a mat...
    except Exception as e:
        print(e)