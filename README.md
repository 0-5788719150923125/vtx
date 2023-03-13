# src

"What is this place?" you ask.

Mike shakes his head and laughs, %HESITATION% "You wouldn't understand."

"Go play in the lab."

# API

- http://localhost:9666/channel
- http://localhost:9666/message
- http://localhost:9666/daemon

# Interface

- https://thesource.fm/
- https://discord.gg/Hv7DEW63Tp

# Training data

- https://ink.university/
- [https://fate.agency/](https://bafybeigz5tzb7kbxeeb6fd7bka5dk3lxuh4g5hujvszaad4xwyw2yjwhne.ipfs.nftstorage.link/)
- [https://research.gq/](https://research.gq/#/page/getting%20started)
- [The Pile](https://bafybeiftud3ppm5n5uudtirm4cf5zgonn44no2qg57isduo5gjeaqvvt2u.ipfs.nftstorage.link/)

# Dashboard

- http://localhost:6006
- http://health.petals.ml/
- [Cockpit](http://localhost:9667)

# Mirrors

- https://chatbook.dev/
- https://chatbook.org/
- http://Alpha8.888/?channel=backbone.lumbar.6/
- http://Omega8.888.ipns.localhost:8080/?channel=backbone.lumbar.5/

# Instructions

- Clone this repo.
- Install Docker.
- `git submodule init` to fetch remote datasets.
- Place configurations into lab/config.yml. [default.yml](./vtx/default.yml)
- Put credentials into a .env file at the root of this project. [example.env](./example.env)
- Put new datasets into lab/{dataset_name}. Also specify them in config.yml.
- Use VSCode tasks as a reference.
- The "build" task will build a Docker image from source files.
- The task "i" is used for data retrieval and preparation tasks.
- The "train" task is used to train your models.
- The "up" task is used to run your bot.
- Ask me questions.
