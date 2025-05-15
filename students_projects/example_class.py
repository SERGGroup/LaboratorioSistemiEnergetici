from main_code.dynamic_classes.student_abstract_class import AbstractStudentClass, keyboard
from REFPROPConnector import ThermodynamicPoint
import numpy as np


class Evaporator(AbstractStudentClass):

    @staticmethod
    def get_shared_params() -> dict:

        # DEFINE AND INITIALIZE THE PARAMETER THAT YOU WOULD LIKE TO CONTROL
        # (you can the use them in the "update_thermo" function line this:
        # "shared_params['m_in_perc'].value". You can modify these values using
        # the keyboard)
        return {'m_out_perc': 50.0, 'm_in_perc': 100.0}

    def init_internal_parameters(self):

        # INSERT HERE THE CODE DEFINED BEFORE THE WHILE LOOP
        liquido = "n-pentane"

        self.tp = ThermodynamicPoint([liquido], [1.])
        self.tp_liq = ThermodynamicPoint([liquido], [1.])
        self.tp_vap = ThermodynamicPoint([liquido], [1.])

        # DATI INIZIALI
        self.T_in = 20
        self.V_in = 1
        self.V_x = 0.5
        self.q_in = 600
        self.m_base = 1

        #   TEMPERATURA INIZIALE
        self.tp.set_variable("T", self.T_in)
        self.tp.set_variable("Q", 0)
        self.p_sat = self.tp.get_variable("P")

        #   CONDIZIONI LIQUIDO SATURO
        self.tp_liq.set_variable("T", self.T_in)
        self.tp_liq.set_variable("Q", 0)
        self.h_l = self.tp_liq.get_variable("h")
        rho_l = self.tp_liq.get_variable("rho")
        m_l = rho_l * self.V_x

        #    CONDIZIONI VAPORE SATURO
        self.tp_vap.set_variable("T", self.T_in)
        self.tp_vap.set_variable("Q", 1)
        self.h_v = self.tp_vap.get_variable("h")
        rho_v = self.tp_vap.get_variable("rho")
        m_v = rho_v * self.V_in * (1 - self.V_x)

        #    MASSA, TITOLO, ENTALPIA MEDIA A T = T_in
        self.m_tot = m_v + m_l
        self.x = m_v / self.m_tot
        self.h_tot = self.h_v * self.x + self.h_l * (1 - self.x)

    def update_thermo(self, dt, shared_params=None):

        # INSERT HERE THE CODE DEFINED INSIDE THE WHILE LOOP

        if self.m_tot <= 0:
            self.m_tot = 0

        m_in = self.m_base * shared_params['m_in_perc'].value / 50
        m_out = self.m_base * shared_params['m_out_perc'].value / 50

        dm = (m_in - m_out) * dt
        dh = ((dt * (m_in * self.h_l - m_out * self.h_v + self.q_in)) - self.h_tot * dm) / self.m_tot

        self.m_tot += dm
        self.h_tot += dh

        # nuove condizioni
        self.tp.set_variable("H", self.h_tot)
        self.tp.set_variable("rho", self.m_tot / self.V_in)
        self.p_sat = self.tp.get_variable("P")

        # memorizzo variabili di interesse
        self.x = self.tp.get_variable("Q")

        if 0 < self.x < 1:

            # aggiorno le entalpie a condiz. di vapor saturo e liquido saturo
            self.tp_liq.set_variable("Q", 0)
            self.tp_liq.set_variable("P", self.tp.get_variable("P"))

            self.tp_vap.set_variable("Q", 1)
            self.tp_vap.set_variable("P", self.tp.get_variable("P"))
            rho_v = self.tp_vap.get_variable("rho")

            self.V_x = 1 - self.x * self.m_tot / rho_v * self.V_in

            self.h_l = self.tp_liq.get_variable("h")
            self.h_v = self.tp_vap.get_variable("h")

        else:

            self.V_x = self.x

    def export_variables(self) -> np.ndarray:

        # RETURN AN ARRAY WITH THE VARIABLES TO BE PLOTTED
        # (The first of the list will be considered the "X"
        # of the plot so always start with time!)
        return np.array([self.t, self.V_x, self.p_sat])

    @property
    def y_labels(self) -> list:
        # RETURN AN ARRAY WITH THE NAMES OF THE VARIABLES TO BE PLOTTED
        # (The first of the list will be considered the "X" so you
        # should not include it!)
        return ["Level [m]", "Pressure [MPa]"]

    def keyboard_listener(self, key_pressed, shared_params):

        # DECIDE WHICH KEY TO PRESS TO UPDATE EACH VALUE
        # Do not use the esc button or the arrow_left and arrow_right

        if key_pressed == keyboard.Key.up:
            # Increase flow rate by 1% up to 100%
            if shared_params['m_out_perc'].value < 100:
                shared_params['m_out_perc'].value += 1.

        elif key_pressed == keyboard.Key.down:
            # Decrease flow rate by 1% down to 0%
            if shared_params['m_out_perc'].value > 0:
                shared_params['m_out_perc'].value -= 1

        elif key_pressed == keyboard.Key.page_up:
            if shared_params['m_in_perc'].value < 100:
                shared_params['m_in_perc'].value += 1.

        elif key_pressed == keyboard.Key.page_down:
            # Decrease flow rate by 1% down to 0%
            if shared_params['m_in_perc'].value > 0:
                shared_params['m_in_perc'].value -= 1
