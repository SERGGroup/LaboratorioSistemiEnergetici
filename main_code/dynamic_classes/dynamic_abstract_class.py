from REFPROPConnector import DiagramPlotter
from abc import ABC, abstractmethod
from pynput import keyboard
import numpy as np


class AbstractDynamicModel(ABC):

    t = 0.0

    def initialize(self):
        self.t = 0.0
        self.init_internal_parameters()

    @abstractmethod
    def init_internal_parameters(self):
        pass

    def update(self, dt, shared_params=None):

        self.t += dt
        self.update_thermo(dt, shared_params)

    @abstractmethod
    def update_thermo(self, dt, shared_params=None):
        pass

    @abstractmethod
    def export_variables(self) -> np.ndarray:
        pass

    def on_key_pressed(self, key_pressed, stop_flag, shared_params) -> bool:

        if key_pressed == keyboard.Key.esc:
            print("Esc pressed! Terminating all processes...")
            stop_flag.set()
            shared_params['pause'].value = False
            return False

        elif key_pressed == keyboard.Key.right:
            shared_params['dt_%'].value += 0.05

        elif key_pressed == keyboard.Key.left:
            if shared_params['dt_%'].value > 0.05:
                shared_params['dt_%'].value -= 0.05

        elif key_pressed == keyboard.Key.space:
            shared_params['pause'].value = (not shared_params['pause'].value)

        else:
            self.keyboard_listener(key_pressed, shared_params)
            return True

    @staticmethod
    @abstractmethod
    def get_shared_params() -> dict:
        pass

    @abstractmethod
    def keyboard_listener(self, key_pressed, shared_params):
        pass

    @property
    @abstractmethod
    def y_labels(self) -> list:
        pass

    @property
    def x_label(self) -> str:
        return 'Time (s)'


class AbstractDynamicModelThermo(AbstractDynamicModel, ABC):
    @abstractmethod
    def export_thermo_plot_variables(self) -> np.ndarray:
        return np.array([])

    @abstractmethod
    def init_diagram_plotter(self) -> DiagramPlotter:
        pass
