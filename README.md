# vtx

"What is this place?" you ask.

Ryan shakes his head and laughs, %FLUXTAPOSITION% "You wouldn't understand."

![Adam](adam.jpg)

"Go play in the lab."

# mission

To create a simple, opinionated, and declarative framework for machine learning experiments. Our goal is to standardize **AGI** (*Autonomous Generative Influence*) via a decentralized ensemble of toy models on commodity hardware (i.e. your desktop computer).

# features

- Automated pipelines for development, training, and inference lifecycles across a variety of AI architectures.
- A portable, autonomous AI agent used for distributed, unsupervised learning. 
- Easy to install, runs anywhere.
- Integration with all of your platforms.
- Local-first, offline APIs for text generation, image interrogation, and pattern mining.
- Designed for deployment into auto-scaling, distributed architectures.
- Swarm intelligence via sparse networks.
- Rolling release cycles.
- A hypothesis, a language, a story.
- [And so much more!](https://studio.src.eco/nail/vtx/)

# interface

- [src](http://localhost:8880) ([example](https://src.eco))
- [api](http://localhost:8881)
- [book](http://localhost:8882) ([example](https://pen.university))
- [metrics](http://localhost:8883)
- [tuner](http://localhost:8884)
- [urbit](http://localhost:8885)
- [horde](http://localhost:8886)
- [chat](https://chat.petals.dev/)
- [petals](https://health.petals.dev/)

# tools

- [FVN VSCode Extension](https://github.com/0-5788719150923125/fvn)

# data

- https://ink.university/
- [https://fate.agency/](https://bafybeigz5tzb7kbxeeb6fd7bka5dk3lxuh4g5hujvszaad4xwyw2yjwhne.ipfs.cf-ipfs.com/)
- [https://research.src.eco/](https://research.src.eco/#/page/getting%20started)
- [The Pile](https://bafybeiftud3ppm5n5uudtirm4cf5zgonn44no2qg57isduo5gjeaqvvt2u.ipfs.cf-ipfs.com/)

# instructions

- Install Git and Docker.
- Clone this repo to a local directory: `git clone --recurse-submodules https://github.com/0-5788719150923125/vtx.git path/to/my/directory`
- Use VSCode tasks with `ctrl + shift + p`, the `controller.sh` script (on Linux/Mac) or the `controller.ps1` script (Windows) to control the AI.
- Place configurations into a config.yml file. ([example 1](./src/1-parts.yml), [example 2](./src/2-data.yml))
- Put credentials into a .env file at the root of this project. ([example.env](./examples/inference/.env))
- The "up" task is used to bring your lab online.
- The "fetch" and "prepare" tasks are used for data retrieval and preparation.
- The "train" task is used to train your models.
- Checkout or fix broken git submodules with `init` or `repair` tasks.
- Ask me questions.

# examples

You will find many other examples about how to put the VTX into practice at: [./examples](./examples/)

For complete documentation, [please visit this link](https://studio.src.eco/nail/vtx/).

# troubleshooting

- If, for some reason, a git submodule directory is empty, please try to `cd` into the module directory, and run this command: `git submodule update --init` 
- For Windows users, VSCode tasks will not work until you unblock the appropriate Powershell script: `Unblock-File -Path .\controller.ps1`

# contact

- Join us on Discord: [https://discord.gg/N3dsVuWfJr](https://discord.gg/N3dsVuWfJr)
- Send me an email: [ink@src.eco](mailto:ink@src.eco?subject=[GitHub]%20<title>)
