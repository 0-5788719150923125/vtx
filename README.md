# vtx

"What is this place?" you ask.

Ryan shakes his head and laughs, %FLUXTAPOSITION% "You wouldn't understand."

![Adam](adam.jpg)

"Go play in the lab."

# mission

To model a simple, opinionated framework for human cloning experiments. Our goal is to standardize AGI (Autonomous Generative Influence) via a decentralized ensemble of toy models, on commodity hardware (i.e. your desktop computer).

# features

- Automated pipelines for development, training, and inference lifecycle tasks across a variety of AI architectures.
- A portable AI agent with support for controlled environments, and unsupervised learning. 
- Easy to install, runs anywhere.
- Integration with a dozen social media platforms.
- Local, offline-first APIs for text generation, image interrogation, and pattern mining.
- Designed for auto-scaling, distributed architectures.
- Swarm intelligence.
- Rolling release cycles.
- A hypothesis, a language, a story.
- [And much more!](https://studio.src.eco/nail/vtx/)

# interface

- [src](http://localhost:9666) ([example](https://src.eco))
- [book](http://localhost:42000) ([example](https://pen.university))
- [metrics](http://localhost:6006)
- [Optuna](http://localhost:6007)
- [Urbit](http://localhost:9099)
- [Petals](https://health.petals.dev/)

# tools

- [FVN VSCode Extension](https://github.com/0-5788719150923125/fvn)

# data

- https://ink.university/
- [https://fate.agency/](https://bafybeigz5tzb7kbxeeb6fd7bka5dk3lxuh4g5hujvszaad4xwyw2yjwhne.ipfs.nftstorage.link/)
- [https://research.src.eco/](https://research.src.eco/#/page/getting%20started)
- [The Pile](https://bafybeiftud3ppm5n5uudtirm4cf5zgonn44no2qg57isduo5gjeaqvvt2u.ipfs.nftstorage.link/)

# instructions

- Install Git and Docker.
- Clone this repo to a local directory: `git clone --recurse-submodules https://github.com/0-5788719150923125/vtx.git path/to/my/directory`
- Checkout the correct branches with: `git submodule foreach 'git reset --hard && git checkout . && git clean -fdx'`
- Place configurations into a config.yml file. ([example](./src/1-parts.yml))
- Put credentials into a .env file at the root of this project. ([example.env](./examples/inference/.env))
- Use VSCode tasks, or the `controller.sh` script (on Linux/Mac) and/or the `controller.ps1` script on Windows.
- The "up" task is used to bring your lab online.
- The "fetch" and "prepare" tasks are used for data retrieval and preparation.
- The "train" task is used to train your models.
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
