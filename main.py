from focuscapsule.runtime_env import prepare_runtime_env


prepare_runtime_env()

from focuscapsule.qt_app import launch_qt_app


if __name__ == "__main__":
    launch_qt_app()
