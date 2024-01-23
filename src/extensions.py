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


# https://huggingface.co/state-spaces/mamba-2.8b/discussions/2
# https://github.com/state-spaces/mamba/blob/main/mamba_ssm/modules/mamba_simple.py
def register_mamba():
    pass
    # from mamba_ssm.models.config_mamba import MambaConfig
    # from mamba_ssm.models.mixer_seq_simple import MambaLMHeadModel

    # AutoConfig.register("mamba", MambaConfig)
    # AutoModelForCausalLM.register(MambaConfig, MambaLMHeadModel)
