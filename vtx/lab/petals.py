import threading
import asyncio
import torch
from transformers import AutoTokenizer
from petals import AutoDistributedModelForCausalLM

loaded_model = None

async def orchestrate():
    print('trying petals')
    try:
        loop = asyncio.get_event_loop()

        # Start a separate thread to load the model
        model_loading_thread = threading.Thread(target=load_model)
        model_loading_thread.start()

        while loaded_model is None:
            await asyncio.sleep(1)
    except Exception as e:
        print(e)

def load_model():
    global loaded_model
    model = AutoDistributedModelForCausalLM.from_pretrained("bigscience/bloomz", cache_dir="models", torch_dtype=torch.float32)
    loaded_model = model
    tokenizer = AutoTokenizer.from_pretrained("bigscience/bloomz", cache_dir="models")
    inputs = tokenizer("A cat sat", return_tensors="pt")["input_ids"]
    outputs = model.generate(inputs, max_new_tokens=5)
    print(tokenizer.decode(outputs[0]))  # A cat sat on a mat...

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(orchestrate())