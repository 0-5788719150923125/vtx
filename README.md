# vtx

"What is this place?" you ask.

Mike shakes his head and laughs, %FLUXTAPOSITION% "You wouldn't understand."

![Adam](adam.jpg)

"Go play in the lab."

# mission

To build a non-trivial, opinionated framework for human cloning experiments. Our goal is to standardize AGI (Adaptive Generative Interfaces) through small models, on commodity hardware (i.e. your desktop computer).

# interface

- [book](http://localhost:42000)
- [src](http://localhost:9666)
- [IPFS](http://localhost:9090)
- [TensorBoard](http://localhost:6006)
- [Urbit](http://localhost:9099)

# data

- https://ink.university/
- [https://fate.agency/](https://bafybeigz5tzb7kbxeeb6fd7bka5dk3lxuh4g5hujvszaad4xwyw2yjwhne.ipfs.nftstorage.link/)
- [https://research.src.eco/](https://research.src.eco/#/page/getting%20started)
- [The Pile](https://bafybeiftud3ppm5n5uudtirm4cf5zgonn44no2qg57isduo5gjeaqvvt2u.ipfs.nftstorage.link/)

# instructions

- Clone this repo.
- Install Docker.
- `git submodule update --init --recursive` to fetch remote datasets.
- Place configurations into src/config.yml. ([default.yml](./src/default.yml))
- Put new datasets into lab/{dataset_name}. Also specify them in config.yml.
- Put credentials into a .env file at the root of this project. ([example.env](./examples/lab/.env))
- Use VSCode tasks as a reference.
- The "build" task will build a Docker image from source files.
- The "fetch" and "prepare" tasks are used for data retrieval and preparation.
- The "train" task is used to train your models.
- The "up" task is used to run your lab.
- Ask me questions.

For thorough documentation, [please visit this link](https://studio.src.eco/nail/vtx/).