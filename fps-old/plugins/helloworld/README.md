# FPS Hello World!

This is a simple example of to create a plugin for [FPS](https://github.com/adriendelsalle/fps).

## Run it!

Just create a fresh environment with `python`, then:

- install `fps-helloworld` with `pip` by running `pip install fps-helloworld`
- run `fps` or `helloworld` command

## Configuration

To give an example of the configuration system of `FPS`, you can create a `toml` file with the following content:

```
[helloworld]
random = false
```

If the config file is named either `fps.toml` or `helloworld.toml`, and the file is in the current working directory (where you run the CLI), it will be automatically registered.

You can also provide a file named differently but then you have to pass it as a CLI argument `fps --config=foo.toml`.
