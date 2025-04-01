from pynput import keyboard
import time


def on_key_event(event):
    print(f"Key pressed: {event.name}")


if __name__ == "__main__":

    with keyboard.Listener(on_press=on_key_event) as listener:
        listener.join()
