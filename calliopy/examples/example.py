from calliopy.core.annotations import Scene
from calliopy.core.app import CalliopyApp


@Scene()
def scene():
    pass


if __name__ == "__main__":
    app = CalliopyApp("calliopy.examples.example")
    app.run()
