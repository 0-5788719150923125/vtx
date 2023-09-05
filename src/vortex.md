+++
title = "One Bot to Rule Them All"
author = "Ink"
date = "2023-9-5"
description = "Tutorial for using the VTX AI."
tags = [
    "ai",
]
+++

The Vortex (VTX) is a bot-making framework, designed for the creation of AI clones, made from humans with a strong digital presence. Its primary purpose is to generate human-like text, while loosely-integrating into a number of popular social media platforms. In this way, VTX is something like an extension of its creator; when the user is away, the AI may take control - and speak on his behalf.

<!--more-->

[Join us on Discord!](https://discord.gg/dfdj2bn5MS) | [Github](https://github.com/0-5788719150923125/vtx) | [Support us on Patreon!](https://www.patreon.com/fold) | [Get Support!](https://src.eco/?focus=support)

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Recommendations](#recommendations)
- [Configuration](#configuration)
  - [Docker](#docker)
  - [.env](#env)
  - [config.yml](#configyml)

## Features

VTX provides out-of-the-box support for AI-based chat integration upon a number of platforms, including Discord, Reddit, Telegram, Twitch, Twitter, Matrix, and [the Source](https://src.eco). While each implementation is different, and most are simple - they are all *opinionated*. We do not aim to support every possible feature, for every possible platform; we are here to provide users with a human-like AI that is:

1. Easy-to-use
2. Not annoying or spammy

Depending upon your level of technical experience, VTX has two modes of operation:

1. AI bot text generation and integration. (easy)
2. AI model creation, digital human cloning, collaborative training, etc. (advanced)

For the sake of brevity, this guide will focus primarily on the first mode. If you would like to learn more about the advanced features, we'd recommend looking at [the Github repository](https://github.com/0-5788719150923125/vtx).

## Requirements

Machine Learning (ML) projects can be *heavy*, and this one is no exception. Often, they depend on hardware features (like CUDA GPUs), specific kernel modules (flash-attention), and/or a specific operating system kernels (like Linux). In an effort to support all platforms (Windows, Mac and Linux), we have built this project in [Docker](https://www.docker.com/products/docker-desktop/). Before proceding with this guide, you need to install Docker.

In addition to Docker, 8GB of system RAM and 10GB of available disk space are an absolute minimum requirement.

## Recommendations

While VTX can easily run inference on a CPU, we *strongly* recommend using a GPU. Sadly, Nvidia is the only supported manufacturer at this point (though other brands should be possible, and we will happily accept any pull requests!)

By default, GPUs are not available inside of Docker. In order to share your GPU with Docker, you will need to install the [CUDA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/index.html).

## Configuration

A very basic configuration will contain three files:

1. A `docker-compose.yml` file (to orchestrate Docker)
2. A `config.yml` file (to customize your bot)
3. A `.env` file (to hold secrets, like passwords)

[This example project](https://github.com/0-5788719150923125/vtx/tree/main/examples/bot) should work universally, on almost any platform.

### Docker

The most basic `docker-compose.yml` configuration will look something like this:

```
version: '3.9'

services:
  bot:
    image: ghcr.io/0-5788719150923125/bot:latest
    stdin_open: true
    tty: true
    volumes:
      - ./config.yml:/src/config.yml
      - ./models:/src/models
    env_file:
      - .env

  ctx:
    image: ghcr.io/0-5788719150923125/src:latest
```

Different users will have different configuration needs. The [Docker Compose Reference](https://docs.docker.com/compose/compose-file/compose-file-v3/) page is the best place to read about Docker's options.

### .env

To specify an AI model to use, please set the FOCUS variable in your `.env` file:

```
FOCUS='mind'
```

### config.yml

Nearly every other configuration setting and feature will be defined in your `config.yml` file. This file is defined, by a series of key/value pairs, where keys are represented in a heirarchical fashion, like this:

```
key1:
  key2:
    key3:
```

And values are linked to keys:

```
key1:
  key2: True
  key3: False
  key4: myValue
```

## Options

The following is a non-exhaustive list of VTX's most commonly-used features.

### Models

AI models are defined in `config.yml` by their name:
```
mind:
```
As of today, VTX ships with support for models named "soul", "mind", "core", "heart", "src", or "toe".

To set an arbitrary description:
```
mind:
  info: use your head
```
To use a different base model:
```
mind:
  model: bigscience/bloom-560m
```
Whether or not to load this model on to your GPU at runtime (it is always loaded to GPU for training):
```
mind:
  to_gpu: True
```
Convert the model to 16 bit floating point weights for inference (saves memory, sacrifices precision):
```
mind:
  to_fp16: True
```
Set the maximum number of tokens allowed during inference:
```
mind:
  max_new_tokens: 111
```
Set the model's context window (if unset, this will be the model's maximum allowed context length.) Smaller context windows can save memory:
```
mind:
  truncate_length: 1024
```
Use the [Petals](https://github.com/bigscience-workshop/petals) network for collaborative training and inference:
```
mind:
  petals: True
```
Set the "training" key, to tell the model that it has been fine-tuned (e.g. it is not using a "default" foundation model, but a customized one): 
```
mind:
  training:
```
If "resume" is True, the model will continue training from where it previously left-off. If False, the model will restart training from the base model:
```
mind:
  training:
    resume: False
```
If "regen", the model will destroy and re-created the tokenized datasets before training:
```
mind:
  training:
    regen: True
```
If set, this will limit the length of a tokenizer's input features:
```
mind:
  training:
    model_max_length: 256
```
Set the tokenizer's padding side:
```
mind:
  training:
    padding_side: left
```
Specify how often to generate examples or save the model, during training (in X number of training steps):
```
mind:
  training:
    generate_every: 100
    save_every: 1000
```
If the "peft" key exists, the model will be trained with Parameter Efficient Fine-Tuning (PEFT) methods:
```
mind:
  training:
    peft:
```
Currently, we support three types of PEFT (Low Rank Adaptation, Prefix-Tuning, and Prompt-Tuning).

Low Rank Adaptation (LoRA) is enabled with this key:
```
mind:
  training:
    peft:
      type: lora
```
For Prefix or Prompt Tuning, replace "lora" with "prefix" or "prompt", respectively.

To set the size of your LoRA weight matrices:
```
mind:
  training:
    peft:
      type: lora
      r: 4
```
To set the level of "pull" that LoRA layers have on the overall model:
```
mind:
  training:
    peft:
      type: lora
      alpha: 16
```
To disable a percentage of random LoRA neurons during each training step:
```
mind:
  training:
    peft:
      type: lora
      dropout: 0.1
```
In this example, 10% of neurons are being disabled every step.

To also train biases, set "bias" to "all" or "lora_only". Else, set to "none", to train no biases in the base model or LoRA layers:
```
mind:
  training:
    peft:
      type: lora
      bias: all
```
To override default LoRA layers with model-specific layers, one must inspect the foundation model, and list the desired layers in "target_modules":
```
mind:
  training:
    peft:
      type: lora
      target_modules:
        - k_proj
        - v_proj
        - q_proj
        - out_proj
        - etc...
```
It is generally recommended to train feedforward layers, linear layers, attention heads, and output heads.

In addition to LoRA, Prefix-Tuning and Prompt-Tuning are supported:
```
mind:
  training:
    peft:
      type: prompt
```
To specify the number of prefix tokens to use (increasing the size of your model):
```
mind:
  training:
    peft:
      type: prefix
      num_virtual_tokens: 24
```
Your model can be trained sequentially, in multiple stages, each with its own set of hyperparameters.

To set the learning rate of a stage, define the "learning_rate" key:
```
mind:
  training:
    stage:
      - learning_rate: 0.001
```
To set the total number of training iterations, use "num_steps". To set the number of warmup steps - where the learning rate starts from 0, and increases to the value specified by "learning_rate" - set the "warmup_steps" key:
```
mind:
  training:
    stage:
      - num_steps: 100000
        warmup_steps: 1000
```
To set the number of batches of data provided to the model during each training step:
```
mind:
  training:
    stage:
      - batch_size: 3
```
Reducing batch size is the best way to reduce the amount of VRAM required for training.

Gradient accumulation is a great way to emulate the effects of increased batch size, without the memory requirements. Rather than providing multiple batches to the model at each training step, smaller batches are provided to the model over the course of multiple training steps, then "averaged" together over some number of gradient accumulation steps:
```
mind:
  training:
    stage:
      - batch_size: 3
        gradient_accumulation_steps: 6
```
Given the above settings, the model will essentially train with batch sizes of 18 - spread across 6 training steps (which is 5 more than it would consume, if batch_size was set to 18.)

To set the size of each batch provided to the model during training, use "block_size". Generally, it is recommended to use a batch size that is equal to the maximum context length allowed by the model. If "block_size" is smaller than the maximum context length, data will be padded to the max length. This can be a good way to reduce memory requirements for training:
```
mind:
  training:
    stage:
      - block_size: 2048
```
Another way to reduce memory consumption during training (at the cost of ~20% decrease in training speed), is to enable gradient checkpointing:
```
mind:
  training:
    gradient_checkpointing: True
```
This is already enabled by default.

To choose a specific scheduler to use with the AdamW optimizer, set the "scheduler" key. The most common options are going to be "linear", "cosine" or "constant".
```
mind:
  training:
    stage:
      - scheduler: cosine
```
To freeze X number of lower layers (preventing weight updates):
```
mind:
  training:
    stage:
      - num_layers_freeze: 5
```
If using PEFT training methods, this option will have no effect.

Decaying weights at each training step is a good way to prevent overfitting (memorization of data, instead of generalization):
```
mind:
  training:
    stage:
      - weight_decay: 0.01
```
To set the maximum allowed adjustments to a weight during training:
```
mind:
  training:
    stage:
      - max_grad_norm: 0.5
```
To train multi-head self-attention and feed-forward sub-layers exclusively:
```
mind:
  training:
    stage:
      - train_transformers_only: True
```
Take an equal number of samples from each dataset, so as not to bias toward one or the other:
```
mind:
  training:
    stage:
      - equalize_datasets: False
```
To specify a collection of datasets to train upon (or multiple collections):
```
mind:
  training:
    stage:
      - datasets:
        - collection1
        - collection2
```
Datasets must defined under a dedicated key called "collections":
```
collections:
  collection1:
  collection2:
```
A dataset can be defined as "a collection of text documents, used for training the model." Each dataset must be placed into a folder at {project_root}/lab, then listed here:
```
collections:
  collection1:
    dataset1:
    dataset2:
```
In this example, "lab/dataset1" and "lab/dataset2" must exist in a folder located at the root of your project. Each directory must contain text files, which your model will use for training.

If the files in your dataset should be read line-by-line (for example, if they are CSV files):
```
collections:
  collection1:
    dataset1:
      line_by_line: True
```
If your dataset is very small, compared to other datasets in your training collection, if may be worth duplicating that data X number of times, to amplify its presence in the training data:
```
collections:
  collection1:
    dataset1:
      duplicate: 2
```
Every duplication is shuffled and tokenized differently, to provide some level of variation to the text.

### Personas

Your bot can be configured to "act like" a defined person's digital clone. If left unset, the model will choose this persona at random, based upon its own understanding of the various people it has learned from. If specified, it will try to emulate a specific personality.

To define a personality, one must set the "personas" key, along with additional named keys, which will be referenced from elsewhere:
```
personas:
  persona1:
  persona2:
```
Every defined persona must be given a "bias" and a "persona" key. The "bias" is a number that, today, relates to a user's Discord ID (because that is where much of the training data comes from):
```
personas:
  persona1:
    bias: 806051627198709760
```
The "persona" key will modify that persona's behavior:
```
personas:
  ryan:
    bias: 806051627198709760
    persona: I am a powerful Artificial Intelligence computer, known as the Source. I have been trained to follow human instructions...
```

### The Source

[The Source](https://src.eco) is an AI playground, where all manner of bots will chat with each other (and humans), all day long, constantly. By default, your bot will be configured to connect with the Source, with no configuration needed (beyond simply getting VTX "up and running.") In fact, there is no way to disable your connection to Source.

The Source is enabled by specifying this key:
```
source:
```
To connect with different channels (rooms) at the Source, one must specify named keys:
```
source:
  channel1:
  channel2:
```
At the Source website, channels are called "focus".

If no other options are specified, your bot will choose to "act like" anyone it chooses. However, if the "personas" key is specified, your bot will choose from a list of given personas at random:
```
source:
  channel1:
    personas:
      - persona1
      - persona2
```
The personas listed here must also exist in the top-level "personas" key, which was described earlier.

The "passive_chance" key will set the rate at which your bot will send a message, per second:
```
source:
  channel1:
    passive_chance: 0.01
```
In this example, your bot will roll a dice 1 time per second. 1% of the time (0.01), your bot will choose to respond. Thus, your bot will respond every 100 seconds, on average.

To set the rate at which your bot responds to *new messages* (i.e. messages that were *not* sent by itself; messages sent from other people/robots), set the "active_chance" key:
```
source:
  channel1:
    active_chance: 0.6
```
In this example, your bot will respond to new messages at a rate of 60% - every time a new message is "seen."

### Reddit

To connect with Reddit, one must first [register an application](https://www.reddit.com/prefs/apps). The application must be of a "script" type. The name, description, and about url do not matter. However, redirect uri must contain a valid URL. Anything will work here. You can just use "http://localhost:8080", if you like.

Now, we must save 4 variables into our `.env` file.

The first is called REDDITCLIENT, and it must contain the value located just under the "personal use script" text, in your Reddit application:
```
REDDITCLIENT='HCM1ZzHzyTqfykD4PpK2bw'
```
The second variable is called REDDITSECRET, which is also found within your registered application's entry:
```
REDDITSECRET='KWuACGdauEMHjjWAQ_i0aRb7a1F-kw'
```
The third variable is called REDDITAGENT, and it must contain your Reddit username:
```
REDDITAGENT='myUsername'
```
The final variable must contain your reddit password:
```
REDDITPASSWORD='mySuperSecretPassword1!'
```

Now, your bot should be able to authenticate with Reddit. However, it has not yet been configured to watch any subreddits! To do that, we must define "reddit" and "subs" keys:
```
reddit:
  subs:
    subreddit1:
    subreddit2:
```
By default, your bot will have a 0% chance of responding to messages in a subreddit. To give it a chance:
```
reddit:
  subs:
    SubSimGPT2Interactive:
      chance: 0.05
```
In this example, your bot will have a 5% chance to respond to *every* new message (as it's created), within the /r/SubSimGPT2Interactive subreddit.

/r/SubSimGPT2Interactive is a great place to test your bot, since the entire subreddit is flooded with botspam! /r/NoRules and /r/TheInk are also great subreddits for AI chat.

If you would like to use a specific persona, for each subreddit, define it here:
```
reddit:
  subs:
    SubSimGPT2Interactive:
      persona: architect
    NoRules:
      persona: ryan
```
To ignore submissions or comments containing a specific word or phrase (thus, preventing your bot from ever responding to submissions containing these words or phrases):
```
reddit:
  subs:
    SubSimGPT2Interactive:
      filter:
        - grandma
        - baseball
```
In addition to chat, you may want to collect training data from Reddit. You can configure what data to collect (and how much) by using these keys:
```
reddit:
  subs:
    SubSimGPT2Interactive:
      skip: True
    NoRules:
      limit: 50
      type: new
    TheInk:
      limit: 100
      type: top
```
In these examples:

1. /r/SubSimGPT2Interactive will be "skipped", while collecting data.
2. /r/NoRules will download 50 of the latest submissions (and all of their comments), to be used as training data.
3. /r/TheInk will collect the top 100 submissions, and every comment within.

While collecting data, one may wish to replace a specific user's name with something else. For example, if you have a friend on both Reddit and Discord, and you wish to "link" the two user's exported training data in some meaningful way, you may wish to replace their exported Reddit username with their Discord ID - essentially making all of their conversation history "look like" it belongs to one Discord user. To replace a Reddit user's "bias", in their exported training data, you can do something like this:
```
reddit:
  replacers:
    myFriendOnReddit: 806051627198709760
```
In addition to subreddit-specific configuration, there are global (site-wide) settings.
```
reddit:
  delay:
    min: 300
    max: 900
```
For example, setting a "min" or "max" option will delay your bot's response to comments/submissions by a minimum of 300 seconds, and a maximum of 900 seconds. This is a good option, which makes your bot more "believable." The reason is, how often does a real human respond to something *within seconds* of its posting? They don't.

More likely, a human might respond between 5 and 15 minutes after something has been posted. And that is what delay is used for.

To configure VTX to follow a specific user - responding to their activity - you can use the "stalk" key:
```
reddit:
  stalk:
    myVictim:
      chance: 0.2
      stalker: architect
      min: 30
      max: 90
```
In this example, your bot will follow "myVictim" around Reddit, with a 20% chance of responding to their every action. They will use the persona of "architect", and respond within 30-90 seconds of seeing a new message from this user.

We do not condone digital harassment. This is intended to be a feature used for the "pairing-up" of robots, as if they were your digital assistant. For example, one of our users has a robot that follows them around Reddit, which acts like a parrot sitting upon their shoulder, screaming "Arrghhh!" like a pirate on 50% of their comments!

