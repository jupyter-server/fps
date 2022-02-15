from .dashboard import Dashboard


def app():
    Dashboard.run(title="API Summary")
