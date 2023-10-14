# vtx

"What is this place?" you ask.

Mike shakes his head and laughs, %FLUXTAPOSITION% "You wouldn't understand."

"Go play in the lab."

# goals

To provide a simple, opinionated framework for human cloning experiments.

# console
```
Swarm state: healthy

...2vYiga, 256.0 RPS  |                                 ########                             |
...vMfXzi, 3688.5 RPS |#########################                                             |
...i9CA9T, 2776.2 RPS |                              ###############                         |
...33Pgb9, 2108.6 RPS |###############                                                       |
...Ap3RUq, 256.0 RPS  |                                     ########                         |
...7mhsNH, 256.0 RPS  |                         ########                                     |
...iRUz6M, 2767.3 RPS |               ###############                                        |
...zbDrjo, 3500.3 RPS |                                             #########################|


Legend:

# - online
J - joining     (loading blocks)
? - unreachable (port forwarding/NAT/firewall issues, see below)
_ - offline     (just disconnected)
```

# interface

- [book](http://localhost:42000)
- [src](http://localhost:9666)
- [IPFS](http://localhost:9090)
- [TensorBoard](http://localhost:6006)

# data

- https://ink.university/
- [https://fate.agency/](https://bafybeigz5tzb7kbxeeb6fd7bka5dk3lxuh4g5hujvszaad4xwyw2yjwhne.ipfs.nftstorage.link/)
- [https://research.gq/](https://research.gq/#/page/getting%20started)
- [The Pile](https://bafybeiftud3ppm5n5uudtirm4cf5zgonn44no2qg57isduo5gjeaqvvt2u.ipfs.nftstorage.link/)

# instructions

- Clone this repo.
- Install Docker.
- `git submodule update --init --recursive` to fetch remote datasets.
- Place configurations into src/config.yml. ([default.yml](./vtx/default.yml))
- Put new datasets into lab/{dataset_name}. Also specify them in config.yml.
- Put credentials into a .env file at the root of this project. ([example.env](./examples/lab/.env))
- Use VSCode tasks as a reference.
- The "build" task will build a Docker image from source files.
- The "i" task is used for data retrieval and preparation tasks.
- The "train" task is used to train your models.
- The "up" task is used to run your lab.
- Ask me questions.

For thorough documentation, [please visit this link](https://studio.src.eco/nail/vtx/).