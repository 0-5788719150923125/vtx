import os
from petals import DistributedBloomForCausalLM

os.environ["TOKENIZERS_PARALLELISM"] = "true"


class bc:
    FOLD = "\033[94m"
    ROOT = "\033[92m"
    CORE = "\033[91m"
    ENDC = "\033[0m"


async def subscribe():
    print(
        bc.FOLD
        + "PEN@FOLD:"
        + bc.ENDC
        + " Downloading BLOOM model. Please wait, this can be very slow."
    )

    model = await DistributedBloomForCausalLM.from_pretrained(
        "bigscience/bloom-petals", tuning_mode="ptune", pre_seq_len=16
    )

    print(bc.ROOT + "ONE@ROOT:" + bc.ENDC + " BLOOM loaded succesfully.")

    # Embeddings & prompts are on your device, BLOOM blocks are distributed across the Internet

    inputs = tokenizer("I think ", return_tensors="pt")["input_ids"]
    outputs = await model.generate(inputs, max_new_tokens=32)
    print(tokenizer.decode(outputs[0]))  # A cat sat on a mat...


# Fine-tuning (updates only prompts or adapters hosted locally)
# optimizer = torch.optim.AdamW(model.parameters())
# for input_ids, labels in data_loader:
#     outputs = model.forward(input_ids)
#     loss = cross_entropy(outputs.logits, labels)
#     optimizer.zero_grad()
#     loss.backward()
#     optimizer.step()
