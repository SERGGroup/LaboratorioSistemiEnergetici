from main_code import CalculatorOptions, run_simulation
from students_projects.example_class import Evaporator

if __name__ == '__main__':

    model = Evaporator()
    options = CalculatorOptions()

    options.time_factor = 100.  # time Acceleration Factor
    options.calculation_frequency = 1000  # Calculation frequency (Hz)
    options.plot_frequency = 30  # plot update frequency (Hz)
    options.buffer_size = 500
    options.draw_thermo_plot = True

    run_simulation(model, options)
