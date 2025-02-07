FPS is a Fast Pluggable System. It was originally designed to create [Jupyverse](https://github.com/jupyter-server/jupyverse), a Jupyter server that is composed of pluggins. But it is a generic framework that can be used to create any type of applications, with the following features:

- **modularity**: an application is made up of modules that are arranged in a hierarchical tree.
- **configuration**: each module can be configured with a set of parameters accessible from the CLI, and an application can be created declaratively as a Python dictionary or a JSON file.
- **pluggability**: modules can share objects, allowing the use of late binding to connect pluggins at runtime.
- **concurrency**: modules have startup and teardown phases for managing asynchronous resources safely.
