from .dynamic_abstract_class import AbstractDynamicModel, keyboard
from REFPROPConnector import ThermodynamicPoint
import numpy as np


class BoilerDynamicModel(AbstractDynamicModel):

    V_in = 0.01         # Internal Volume [m^3]
    q_in = 5            # Power inlet [kW]
    m_in_max = 1        # Maximum flow inlet [kg/s]
    p_in_max = 10       # Maximum inlet pressure [MPa]

    T_0 = 20            # Initial Temperature [°C]
    V_x0 = 0.5          # Initial Liquid Level [-]
    p_out = 0.101325    # Outlet Pressure [MPa]

    def __init__(self):

        self.thermo = None
        self.__tmp_thermo = None

    def init_internal_parameters(self):

        self.thermo = ThermodynamicPoint(["water"], [1])
        self.__tmp_thermo = ThermodynamicPoint(["water"], [1])

        self.T = self.T_0
        self.V_x = self.V_x0

        self.m_dot_in_perc = 0.2
        self.yd_perc = 0.8

        self.thermo.set_variable("T", self.T)
        self.thermo.set_variable("Q", 0.)
        rho_liq = self.thermo.get_variable("rho")
        h_liq = self.thermo.get_variable("h")

        self.P = self.thermo.get_variable("P")
        self.m_dot_out = 0.

        self.thermo.set_variable("T", self.T)
        self.thermo.set_variable("Q", 1.)
        rho_vap = self.thermo.get_variable("rho")
        h_vap = self.thermo.get_variable("h")

        self.m_in = (rho_liq * self.V_x + rho_vap * (1 - self.V_x)) * self.V_in
        x_in =  rho_vap * (1 - self.V_x) * self.V_in / self.m_in
        self.h_in = h_liq * (1 - x_in) + h_vap * x_in

        self.__tmp_thermo.set_variable("P", self.p_in_max)
        self.__tmp_thermo.set_variable("Q", 1.)
        rho_vap_max = self.thermo.get_variable("rho")

        self.yd_max = np.sqrt(self.p_in_max * 1e6 * rho_vap_max) / self.m_in_max

    def evaluate_m_out(self, yd_perc):

        # Treated as a turbine (Stodola Curve)
        p_in = self.thermo.get_variable("P")

        self.__tmp_thermo.set_variable("P", p_in)
        self.thermo.set_variable("Q", 1.)
        rho_vap = self.thermo.get_variable("rho")

        p_ratio = p_in / self.p_out

        if p_ratio < 1:
            return 0.

        if yd_perc > 0:
            yd = 1 / ((1 / self.yd_max) * yd_perc)
            phi_sqr = (1 - 1 / p_ratio ** 2) / yd

        else:
            phi_sqr = 0.

        m_out = np.sqrt(phi_sqr * p_in ** 2 * rho_vap)

        return m_out

    def get_saturation_conditions(self, T):

        self.thermo.set_variable("T", T)
        self.thermo.set_variable("Q", 0.)

        p_sat = self.thermo.get_variable("P")
        rho_liq = self.thermo.get_variable("rho")
        h_liq = self.thermo.get_variable("rho")

        self.thermo.set_variable("T", T)
        self.thermo.set_variable("Q", 1.)
        rho_vap = self.thermo.get_variable("rho")
        h_vap = self.thermo.get_variable("rho")

        return p_sat, rho_vap, rho_liq, h_liq, h_vap

    def update_thermo(self, dt, shared_params=None):

        rho_mean = self.m_in / self.V_in

        self.thermo.set_variable("H", self.h_in)
        self.thermo.set_variable("rho", rho_mean)

        self.T = self.thermo.get_variable("T")
        self.P = self.thermo.get_variable("P")

        p_sat, rho_vap, rho_liq, h_liq, h_vap = self.get_saturation_conditions(self.T)
        self.V_x = (rho_mean - rho_vap) / (rho_liq - rho_vap)

        if shared_params is not None:
            self.m_dot_in_perc = shared_params["m_in_perc"].value / 100
            self.yd_perc = shared_params["yd_perc"].value / 100

        self.m_dot_in = self.m_dot_in_perc * self.m_in_max
        self.m_dot_out = self.evaluate_m_out(self.yd_perc)

        self.m_in = min(max(0., self.m_in + (self.m_dot_in - self.m_dot_out) * dt), self.V_in * rho_liq)
        self.h_in += (self.q_in - self.m_dot_out * h_vap + self.m_dot_in * h_liq) * dt / self.m_in

    def export_variables(self) -> np.ndarray:
        return np.array([self.t, self.T, self.P, self.m_dot_out])

    def keyboard_listener(self, key_pressed, shared_params):
        if key_pressed == keyboard.Key.up:
            # Increase flow rate by 1% up to 100%
            if shared_params['m_in_perc'].value < 100:
                shared_params['m_in_perc'].value += 1.

        elif key_pressed == keyboard.Key.down:
            # Decrease flow rate by 1% down to 0%
            if shared_params['m_in_perc'].value > 0:
                shared_params['m_in_perc'].value -= 1

        if key_pressed == keyboard.Key.delete:
            # Increase flow rate by 1% up to 100%
            if shared_params['yd_perc'].value < 100:
                shared_params['yd_perc'].value += 1.

        elif key_pressed == keyboard.Key.enter:
            # Decrease flow rate by 1% down to 0%
            if shared_params['yd_perc'].value > 0:
                shared_params['yd_perc'].value -= 1

    @property
    def y_labels(self) -> list:
        return ['Temperature (°C)', 'Pressure (MPa)', 'Flow Rate Out (kg/s)']

    @staticmethod
    def get_shared_params() -> dict:
        return {'m_in_perc': 10.0, "yd_perc": 50.}