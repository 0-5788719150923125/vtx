from transformers import (
    AutoConfig,
    AutoModelForCausalLM,
    AutoModelForSequenceClassification,
)


def register_models():
    register_moduleformer()
    register_mamba()


def register_moduleformer():
    from moduleformer import (
        ModuleFormerConfig,
        ModuleFormerForCausalLM,
        ModuleFormerForSequenceClassification,
    )

    AutoConfig.register("moduleformer", ModuleFormerConfig)
    AutoModelForCausalLM.register(ModuleFormerConfig, ModuleFormerForCausalLM)
    AutoModelForSequenceClassification.register(
        ModuleFormerConfig, ModuleFormerForSequenceClassification
    )


# Should be easy to implement:
# https://huggingface.co/state-spaces/mamba-2.8b/discussions/2
def register_mamba():
    pass
