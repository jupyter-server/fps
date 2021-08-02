from setuptools import setup

setup(
    name="fps_some",
    install_requires=["fps"],
    entry_points={
        "fps": ["fps_some = some.main"],
        "console_scripts" : "some = some.cli:app"
    }
)