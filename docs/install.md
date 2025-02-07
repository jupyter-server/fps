FPS can be installed through [PyPI](https://pypi.org) or [conda-forge](https://conda-forge.org).

## With `pip`

```bash
pip install fps[web]
```

## With `micromamba`

We recommend using `micromamba` to manage `conda-forge` environments (see `micromamba`'s
[installation instructions](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html)).
First create an environment, here called `my-env`, and activate it:
```bash
micromamba create -n my-env
micromamba activate my-env
```
Then install `fps`.

```bash
micromamba install fps
```

## Development install

You first need to clone the repository:
```bash
git clone https://github.com/jupyter-server/fps.git
cd fps
```
We recommend working in a conda environment. In order to build `fps`, you will need
`pip`:
```bash
micromamba create -n fps-dev
micromamba activate fps-dev
micromamba install pip
```
Then install `fps` in editable mode:
```bash
pip install -e ".[web,test,docs]"
```
