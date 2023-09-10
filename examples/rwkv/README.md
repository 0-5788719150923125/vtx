# RWKV bug

This demo exists to reproduce a problem in the RWKV inference code.

To build the Docker image:
```
docker compose build
```

To run the Docker image:
```
docker compose up
```

To reproduce the bug, switch between `model.eval()` and `model.train()`.

When set to `model.train()`, results are consistent with expectations:
```
Hello world!

¶806051627198709760:> I'm not sure what you're talking about.
¶806051627198709760:> I'm not sure what you're talking about.
¶806051627198709760:> I'm not sure what you're talking about.
¶806051627198709760:> I'm not sure what you're talking about.
¶806051627198709760:
```

When set to `model.eval()`, output is usually gibberish:
```
Hello world! ¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶
```