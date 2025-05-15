from main_code.dynamic_classes.dynamic_abstract_class import AbstractDynamicModelThermo, keyboard
from REFPROPConnector import DiagramPlotter, DiagramPlotterOptions
from abc import ABC
import numpy as np


class AbstractStudentClass(AbstractDynamicModelThermo, ABC):

    V_x = 0.5
    p_sat = 0.00
    tp = None

    def export_thermo_plot_variables(self) -> np.ndarray:

        if self.tp is not None:
            return np.array([self.tp.get_variable("rho"), self.tp.get_variable("P")])
        else:
            return np.array([0., 0.])

    def init_diagram_plotter(self) -> DiagramPlotter:

        __tpm_tp = self.tp.duplicate()
        __tpm_tp.set_variable("P", __tpm_tp.RPHandler.PC)
        __tpm_tp.set_variable("T", __tpm_tp.RPHandler.TC)

        x_range = np.array([0.001, 3]) * __tpm_tp.get_variable("rho")
        y_range = np.array([0.001, 3]) * __tpm_tp.get_variable("P")
        t_range = np.array([0.001, 1]) * __tpm_tp.get_variable("T")
        h_range = np.array([0.001, 1]) * __tpm_tp.get_variable("h")
        isoline_ranges = ({

            "T": (t_range[0], t_range[1], 10),
            "H": (h_range[0], h_range[1], 10)

        })

        diag_opt = DiagramPlotterOptions(

            n_isolines_points=100, n_sat_points=100,
            x_variable="rho", x_var_range=x_range, x_var_log=True,
            y_variable="P", y_var_range=y_range, y_var_log=True,
            isoline_ranges=isoline_ranges, plot_saturation=True


        )
        return DiagramPlotter(__tpm_tp, diag_opt)
