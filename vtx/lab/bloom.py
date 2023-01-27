from petals import DistributedBloomForCausalLM

model = DistributedBloomForCausalLM.from_pretrained(
    "bigscience/bloom-petals", tuning_mode="ptune", pre_seq_len=16
)

print(bcolors.ROOT + "ONE@ROOT:" + bcolors.ENDC + " BLOOM loaded succesfully.")

# Embeddings & prompts are on your device, BLOOM blocks are distributed across the Internet

inputs = tokenizer("A cat sat", return_tensors="pt")["input_ids"]
outputs = model.generate(inputs, max_new_tokens=5)
print(tokenizer.decode(outputs[0]))  # A cat sat on a mat...

# Fine-tuning (updates only prompts or adapters hosted locally)
optimizer = torch.optim.AdamW(model.parameters())
for input_ids, labels in data_loader:
    outputs = model.forward(input_ids)
    loss = cross_entropy(outputs.logits, labels)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    FOLD = "\033[96m"
    ROOT = "\033[92m"
    WARNING = "\033[93m"
    CORE = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
