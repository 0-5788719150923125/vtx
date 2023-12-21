# vtx

"What is this place?" you ask.

Mike shakes his head and laughs, %FLUXTAPOSITION% "You wouldn't understand."

![Adam](adam.jpg)

"Go play in the lab."

# mission

To build a simple, opinionated framework for human cloning experiments. Our goal is to standardize AGI (Autonomous Generative Influence) via a decentralized ensemble of toy models, on commodity hardware (i.e. your desktop computer).

# features

- Automated lifecycle tasks for development, training, and inference pipelines across a variety of AI architectures.
- A portable AI agent with support for controlled environments, and unsupervised learning. 
- Easy to install, runs anywhere.
- Integration with a dozen social media platforms.
- Local, offline-first APIs for text generation, image interrogation, and pattern mining.
- Swarm intelligence.
- Rolling release cycles.
- A hypothesis, a language, and a story.
- [And much more!](https://studio.src.eco/nail/vtx/)

# interface

- [book](http://localhost:42000) ([example](https://pen.university))
- [src](http://localhost:9666)
- [metrics](http://localhost:6006)
- [IPFS](http://localhost:9090)
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

- Clone this repo to a local directory: `git clone --recurse-submodules https://github.com/0-5788719150923125/vtx.git path/to/my/directory`
- Checkout the correct branches with: `git submodule foreach 'git reset --hard && git checkout . && git clean -fdx'`
- Install Docker.
- Place configurations into config.yml. ([default.yml](./src/default.yml))
- Put new datasets into lab/{dataset_name}. Also specify them in config.yml.
- Put credentials into a .env file at the root of this project. ([example.env](./examples/lab/.env))
- Find many other examples in [./examples](./examples/).
- Use VSCode tasks as a reference.
- The "build" task will build a Docker image from source files.
- The "fetch" and "prepare" tasks are used for data retrieval and preparation.
- The "train" task is used to train your models.
- The "up" task is used to run your lab.
- Ask me questions.

For complete documentation, [please visit this link](https://studio.src.eco/nail/vtx/).

# troubleshooting

- If, for some reason, a git submodule directory is empty, please try to `cd` into the module directory, and run this command: `git submodule update --init` 

# contact

- Join us on Discord: [https://discord.gg/N3dsVuWfJr](https://discord.gg/N3dsVuWfJr)
- Send me an email: [ink@src.eco](ink@src.eco)