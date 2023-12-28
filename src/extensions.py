from transformers import (
    AutoConfig,
    AutoModelForCausalLM,
    AutoModelForSequenceClassification,
)


def register_models():
    register_moduleformer()


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
