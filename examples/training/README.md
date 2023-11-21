# Training demo
---

In this example, we will show you how to quickly fine-tune a small GPT-Neo model, and connect it to [The Source](https://src.eco).

This work assumes that you already have some familiarity with AI, git, Docker, and this project. You also need to have all required dependencies (mainly Docker and a GPU).

[See here](https://studio.src.eco/nail/vtx/) for complete documentation.

## The process

### 1. Obtain project files

Clone the entire project to a folder on your desktop:
```
git clone --recurse-submodules https://github.com/0-5788719150923125/vtx.git path/to/my/directory
```
Some of these modules will ask for a username/password (which you will not have). That's okay, just skip them with:
```
Enter
```

### 2. Create your configuration files

In the root of your project directory, create a file called `.env`. This file contains all of your secrets. DO NOT SHARE IT WITH ANYONE.

You may copy a template `.env` file from here: [example.env](https://github.com/0-5788719150923125/vtx/blob/main/examples/lab/.env)

Next, create a file called `config.yml` in the root of your project. We can leave this empty for now.

### 3. Test your live environment

By default, this project should function without any additional configuration. To quickly test it, use this series of VSCode commands:

1. `Ctrl+Shift+P`
2. `Tasks: Run Task`
3. `up`
4. `toe`

If this works, your AI should progress through the following stages:

1. Download the "lab" and "ctx" Docker images.
2. Launch the Python application.
3. Download the "GPT-Neo 125M" model, and save it to data/models.
4. Attach a LoRA adapter (toe) to the model, and begin running inference (chatting) with [The Source](https://src.eco).

If this works, you are ready to proceed. You can bring down the project in this way:

1. `Ctrl+Shift+P`
2. `Tasks: Run Task`
3. `down`

### 4. Prepare your model for training

When your model came online, it used an adapter that was trained by somebody else. But we want to train our own model!

To do this, we need to take a few steps:

1. Collect and prepare some datasets to train with.
2. Define your model training and dataset configuration.
3. Train the model with your GPU.

Let's begin with data preparation.

### 5. Fetch and prepare a dataset

We are going to use Alexa's [Topical Chat](https://github.com/alexa/Topical-Chat) dataset, because we want to train bots how to chat with humans in a multi-user environment. Whereas most datasets will take a rather simplistic approach to data preparation, ours is quite different:

Theirs:
```
USER: Hello! How are you?
ASSISTANT: I'm well, how are you?
```

Ours:
```
¶806051627198709760:> Hello! How are you?
¶1051104179323678812:> I'm well, how are you?
```

We do this because our bots are given the entire context of a conversation (every single user involved), rather than an isolated, 1-on-1 interaction between two users. I don't know if this is the best way to handle conversational AI - but it's how this project was designed! We're open to better ideas.

Anyway, let's fetch our dataset:

1. `Ctrl+Shift+P`
2. `Tasks: Run Task`
3. `fetch`
4. `ghosts`

This will execute the `fetch.py` script found within lab/ghosts. When finished, you should see the raw data within lab/ghosts/source.

Now, let's transform that data into our special format:

1. `Ctrl+Shift+P`
2. `Tasks: Run Task`
3. `prepare`
4. `ghosts`

This will execute the `prepare.py` script found within lab/ghosts, and output our specially-crafted data into lab/ghosts/train.

### 6. Define our dataset

Now, let's make sure our `config.yml` file is aware of our prepared dataset. For now, let's define a collection called "test", and add our ghosts dataset to it:

```yml
collections:
  test:
    lab/ghosts/train:
```

See how we explicitly point directly to the path containing files we want to use? This is the pattern.

You can actually add multiple directories to a collection - but let's move on for now.

### 7. Define our model and training details

Also in our `config.yml` file, we need to define our model and training configuration. Each one of the following settings could be a topic of their own, but for now, just copy this example:

```yml
toe:
  info: nailed to the foot
  model: EleutherAI/gpt-neo-125M
  training:
    type: "lora"
    r: 4
    alpha: 16
    bias: "none"
    target_modules:
      - k_proj
      - v_proj
      - q_proj
    learning_rate: 0.001
    block_size: 2048
    num_steps: 10000
    warmup_steps: 1000
    weight_decay: 0.01
    gradient_clip_val: 0.5
    scheduler: cosine
    batch_size: 3
    gradient_accumulation_steps: 6
    save_every: 1000
    generate_every: 250
    datasets:
      - test
```

There are many, many other settings to work with. We encourage you to look at the (incomplete) [documentation here](https://studio.src.eco/nail/vtx), or to explore the source code in the [training harness](https://github.com/0-5788719150923125/vtx/blob/main/src/harness.py#L492).

Be aware: "batch_size", "block_size", and the size of your model (GPT-Neo 125M has 125M parameters) has a huge impact on training speed, and VRAM consumption. If training crashes, it's likely that you've run out of VRAM. Reduce these three settings to see if that helps.

### 8. Launch the training

With all configuration in-place, let's begin the training:

1. `Ctrl+Shift+P`
2. `Tasks: Run Task`
3. `train`
4. `toe`

This will launch a Docker container, import your dataset(s), tokenize that data, and begin training.

You can monitor progress via TensorBoard, [here](http://localhost:6006).

### 9. Test the model

When training is complete (or really, after "save_every" number of training steps), you may launch the project, and test your model:

1. `Ctrl+Shift+P`
2. `Tasks: Run Task`
3. `up`
4. `toe`

Your bot will be online, available and chatting in [the trade channel, at the Source](https://src.eco/?focus=trade).

You will also have a local instance of the Source available [here](http://localhost:9666).

Finally, you will see your bot chatting with others in the terminal.

- BLUE: Others/AI/system messages.
- RED: Your bot.
- GREEN: Your bot (using true RNG).

### 10. Have fun!

If you have any questions, feel free to contact us!