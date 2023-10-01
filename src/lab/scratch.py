from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "EleutherAI/pythia-1b-deduped"

tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir="/src/models")
model = AutoModelForCausalLM.from_pretrained(model_name, cache_dir="/src/models")


# inputs = tokenizer("Harry Potter is", return_tensors="pt")["input_ids"]
inputs = None

outputs = model.generate(
    inputs=inputs,
    do_sample=True,
    temperature=0.7,
    eta_cutoff=0.0003,
    penalty_alpha=0.6,
    top_k=4,
    repetition_penalty=2.3,
    no_repeat_ngram_size=9,
    max_new_tokens=222,
)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
