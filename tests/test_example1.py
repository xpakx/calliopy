from calliopy.examples.example2 import scene
from utils import ScriptableDialogueManager


def test_scene_default_choice():
    dial = ScriptableDialogueManager()

    scene(dial)

    assert len(dial.say_log) == 2
    assert dial.say_log[0] == ("Alice", "Hello Bob! Ready for an adventure?")
    assert dial.say_log[1] == ("Bob", "Great! Let's go!")


def test_scene_scripted_choice():
    dial = ScriptableDialogueManager(script=[1])

    scene(dial)

    assert len(dial.say_log) == 2
    assert dial.say_log[1] == ("Bob", "Maybe later then...")
