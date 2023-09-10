from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

tokenizer = AutoTokenizer.from_pretrained("RWKV/rwkv-4-430m-pile", cache_dir="models")
model = AutoModelForCausalLM.from_pretrained(
    "RWKV/rwkv-4-430m-pile", cache_dir="models"
)

model = PeftModel.from_pretrained(model, "adapter")
model.eval()
# model.train()

inputs = tokenizer("Hello world!", return_tensors="pt")["input_ids"]
outputs = model.generate(inputs=inputs, max_new_tokens=100)
print(tokenizer.decode(outputs[0]))
