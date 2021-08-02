from setuptools import setup

setup(
    name="fps_helloworld",
    install_requires=["fps"],
    entry_points={
        "fps": ["fps-helloworld = helloworld.main"],
        "console_scripts": "helloworld = fps.cli:app",
    },
)
