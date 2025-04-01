from pynput import keyboard
import time


def on_key_event(key_code):
    print(f"Key pressed: {key_code}")
    if key_code == keyboard.Key.esc:
        return False


if __name__ == "__main__":

    with keyboard.Listener(on_press=on_key_event) as listener:
        listener.join()

