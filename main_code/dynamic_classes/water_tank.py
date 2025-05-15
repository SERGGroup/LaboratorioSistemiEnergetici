from .dynamic_abstract_class import AbstractDynamicModel, keyboard
import numpy as np


class WaterTankDynamicModel(AbstractDynamicModel):

    g = 9.81  # Gravity [m/s^2]
    rho = 1000  # Density [kg/m^3]
    a_out = 0.005  # Outflow area [m^2]
    a_int = 0.01  # Cross-sectional area of tank [m^2]
    m_in_max = 100.  # Maximum flow rate [kg/s]
    h = 0.
    m_in = 0.

    def init_internal_parameters(self):
        self.h = 0.
        self.m_in = 0.

    def update_thermo(self, dt, shared_params=None):

        v_out = np.sqrt(2 * self.g * self.h)
        if np.isnan(v_out):
            v_out = 0.

        m_out = self.rho * v_out * self.a_out

        if shared_params is None:
            self.m_in = self.m_in_max * 0.5

        else:
            self.m_in = (shared_params["m_in_perc"].value / 100) * self.m_in_max

        self.h += (self.m_in - m_out) * dt / (self.rho * self.a_int)

    def export_variables(self) -> np.ndarray:
        return np.array([self.t, self.h, self.m_in])

    def keyboard_listener(self, key_pressed, shared_params):
        if key_pressed == keyboard.Key.up:
            # Increase flow rate by 1% up to 100%
            if shared_params['m_in_perc'].value < 100:
                shared_params['m_in_perc'].value += 1.

        elif key_pressed == keyboard.Key.down:
            # Decrease flow rate by 1% down to 0%
            if shared_params['m_in_perc'].value > 0:
                shared_params['m_in_perc'].value -= 1

    @property
    def y_labels(self) -> list:
        return ['Height (m)', 'flow rate (kg/s)']

    @staticmethod
    def get_shared_params() -> dict:
        return {'m_in_perc': 50.0}