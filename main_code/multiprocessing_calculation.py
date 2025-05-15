from main_code.dynamic_classes.dynamic_abstract_class import AbstractDynamicModelThermo as AbstractDynamicModel
import multiprocessing.shared_memory as shm
import matplotlib.patches as patches
from multiprocessing import Manager
import matplotlib.pyplot as plt
from pynput import keyboard
import multiprocessing
import numpy as np
import time


class CalculatorOptions:

    dtype = np.float64  # Data type

    # Global variables for timestep and frequency
    time_factor = 1.                # time Acceleration Factor
    calculation_frequency = 1000    # Calculation frequency (Hz)
    plot_frequency = 30             # plot update frequency (Hz)
    buffer_size = 1000              # Buffer Size
    thermo_buffer_size = 1000       # Thermo Buffer Size
    draw_thermo_plot = False        # Activate the diagram plot drawing

    @property
    def dt(self):
        return self.time_factor / self.calculation_frequency

    @property
    def t_sleep_max(self):
        return 1 / self.calculation_frequency

    @property
    def t_sleep_max_plot(self):
        return 1 / self.plot_frequency

    def get_shape(self, model: AbstractDynamicModel):

        n_elements = len(model.export_variables())
        return (self.buffer_size, n_elements)

    def get_thermo_shape(self, model: AbstractDynamicModel):
        n_elements = len(model.export_thermo_plot_variables())
        return (self.thermo_buffer_size, n_elements)


def worker(model: AbstractDynamicModel, options, shared_names, stop_flag, shared_params):

    """Worker function for each calculation step."""
    model.initialize()

    buffer_head = 0
    base_shape = options.get_shape(model)
    existing_shm = shm.SharedMemory(name=shared_names[0])
    buffer_arr = np.ndarray(base_shape, dtype=options.dtype, buffer=existing_shm.buf)

    if options.draw_thermo_plot:
        thermo_buffer_head = 0
        thermo_shape = options.get_thermo_shape(model)
        thermo_shm = shm.SharedMemory(name=shared_names[1])
        thermo_buff_arr = np.ndarray(thermo_shape, dtype=options.dtype, buffer=thermo_shm.buf)

    print("Worker started!")

    mean_sleep_time = 0.
    count = 0.
    while not stop_flag.is_set():

        if not shared_params["pause"].value:

            start_time = time.time()

            # Perform your calculation step
            dt = options.dt * shared_params["dt_%"].value
            model.update(dt, shared_params)

            # Update shared data (buffer)
            exported_variables = model.export_variables()
            buffer_arr[buffer_head, :] = exported_variables
            buffer_head = np.mod(buffer_head + 1, options.buffer_size)

            # Update shared data for thermodynamic plot
            if options.draw_thermo_plot:
                thermo_buff_arr[thermo_buffer_head, :] = model.export_thermo_plot_variables()
                thermo_buffer_head = np.mod(thermo_buffer_head + 1, options.thermo_buffer_size)

            # Calculate the time taken for the current step
            t_sleep_max = options.t_sleep_max
            elapsed_time = time.time() - start_time
            sleep_time = max(0., t_sleep_max - elapsed_time)  # Sleep to ensure dt time step
            mean_sleep_time += sleep_time / t_sleep_max
            count += 1

            time.sleep(sleep_time)  # Sleep for the remainder of the timestep

    mean_sleep_time = mean_sleep_time / count
    occupation = 1 - mean_sleep_time
    print(

        "Worker finished! (mean sleep time {:.2f}ms, cycle occupation: {:.2f}%, iterations: {})".format(
            mean_sleep_time * options.t_sleep_max * 1000,
            occupation * 100,
            count

        )

    )

def plot_results(model: AbstractDynamicModel, options, shared_names, stop_flag):

    model.initialize()

    """Real-time plotting of results."""
    x_label = model.x_label
    y_labels = model.y_labels
    n_rows = len(y_labels)

    plt.ion()  # Turn on interactive mode
    fig, axs = plt.subplots(nrows=n_rows)

    plt.tight_layout()

    for n, ax in enumerate(axs):
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_labels[n])

    plt.tight_layout()

    existing_shm = shm.SharedMemory(name=shared_names[0])
    n_elements = len(model.export_variables())
    shape = (options.buffer_size, n_elements)
    buffer_arr = np.ndarray(shape, dtype=options.dtype, buffer=existing_shm.buf)
    mean_sleep_time = 0.
    count = 0.

    print("Plot started!")

    while not stop_flag.is_set():

        start_time = time.time()
        curr_buffer = buffer_arr.copy()
        sorted_indices = np.argsort(np.nan_to_num(curr_buffer[:, 0], nan=np.inf))
        sorted_buffer = curr_buffer[sorted_indices]

        for n, ax in enumerate(axs):
            ax.clear()
            ax.plot(sorted_buffer[:, 0], sorted_buffer[:, n+1])

            ax.set_xlabel(x_label)
            ax.set_ylabel(y_labels[n])

        fig.canvas.draw_idle()

        plt.pause(0.01)  # Small pause to allow updates

        t_sleep_max = options.t_sleep_max_plot
        elapsed_time = time.time() - start_time
        sleep_time = max(0., t_sleep_max - elapsed_time)  # Sleep to ensure dt time step

        mean_sleep_time += sleep_time / t_sleep_max
        count += 1

        time.sleep(sleep_time)

    plt.ioff()
    mean_sleep_time = mean_sleep_time / count
    occupation = 1 - mean_sleep_time
    print(

        "Plotter finished! (mean sleep time {:.2f}ms, cycle occupation: {:.2f}%, iterations: {})".format(
            mean_sleep_time * options.t_sleep_max_plot * 1000,
            occupation * 100,
            count

        )

    )

def plot_dashboard(shared_params, stop_flag, options):

    plt.ion()
    fig = plt.figure(figsize=(3, 2))

    dashboard_ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
    dashboard_ax.axis('off')

    # Initialize status indicators (light circles)
    indicators = {
        "Running": {"pos": (0.5, 0.85), "color": 'green'},
        "Paused": {"pos": (0.5, 0.65), "color": 'red'},
    }

    circles = {}
    texts = {}

    # Pause light indicators
    for label, props in indicators.items():
        if "color" in props:
            c = patches.Circle(props["pos"], 0.05, color=props["color"])
            dashboard_ax.add_patch(c)
            circles[label] = c
        t = dashboard_ax.text(props["pos"][0] + 0.1, props["pos"][1], label, va='center', fontsize=10)
        texts[label] = t

    # Text indicator for inflow percentage (dt_%)
    inflow_text = dashboard_ax.text(0.5, 0.45, "Time Scale: 50%", ha='center', fontsize=10)

    while not stop_flag.is_set():

        start_time = time.time()

        # Get the current pause state and inflow percentage
        paused = shared_params["pause"].value
        dt_percent = shared_params["dt_%"].value

        # Update text and light status indicators
        inflow_text.set_text(f"Time scale: {dt_percent * 100:.0f}%")

        # Update the pause light status
        circles["Running"].set_color('green' if not paused else 'gray')
        circles["Paused"].set_color('red' if paused else 'gray')

        # Update the figure
        fig.canvas.draw()

        plt.pause(0.01)

        t_sleep_max = options.t_sleep_max_plot
        elapsed_time = time.time() - start_time
        sleep_time = max(0., t_sleep_max - elapsed_time)  # Sleep to ensure dt time step
        time.sleep(sleep_time)

    plt.ioff()

def plot_thermo_plot(model: AbstractDynamicModel, options, shared_names, stop_flag):

    model.initialize()

    plt.ion()
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(7, 5))

    existing_shm = shm.SharedMemory(name=shared_names[1])
    shape = options.get_thermo_shape(model)
    buffer_arr = np.ndarray(shape, dtype=options.dtype, buffer=existing_shm.buf)

    plotter = model.init_diagram_plotter()
    plotter.calculate()

    count = 0
    mean_sleep_time = 0.
    while not stop_flag.is_set():

        start_time = time.time()
        ax.clear()

        curr_buffer = buffer_arr.copy()
        sorted_indices = np.argsort(np.nan_to_num(curr_buffer[:, 0], nan=np.inf))
        sorted_buffer = curr_buffer[sorted_indices]

        plotter.plot(ax)
        ax.plot(sorted_buffer[:, 0], sorted_buffer[:, 1])
        fig.canvas.draw_idle()
        plt.pause(0.01)  # Small pause to allow updates

        t_sleep_max = options.t_sleep_max_plot
        elapsed_time = time.time() - start_time
        sleep_time = max(0., t_sleep_max - elapsed_time)  # Sleep to ensure dt time step

        mean_sleep_time += sleep_time / t_sleep_max
        count += 1

        time.sleep(sleep_time)

    plt.ioff()

    mean_sleep_time = mean_sleep_time / count
    occupation = 1 - mean_sleep_time
    print(

        "Thermo Plotter finished! (mean sleep time {:.2f}ms, cycle occupation: {:.2f}%, iterations: {})".format(
            mean_sleep_time * options.t_sleep_max_plot * 1000,
            occupation * 100,
            count

        )

    )

def keyboard_listener(model, stop_flag, shared_parms):

    print("Listener started!")

    with keyboard.Listener(on_press=lambda key: model.on_key_pressed(key, stop_flag, shared_parms)) as listener:
        listener.join()

    print("Listener finished!")

def run_simulation(model: AbstractDynamicModel, options: CalculatorOptions):

    manager = Manager()
    stop_flag = manager.Event()

    shared_params = {

        "dt_%": multiprocessing.Value('d', 1.),
        "pause": multiprocessing.Value("b", False)

    }
    main_shared_param = model.get_shared_params()
    for key in main_shared_param:
        shared_params.update({key: multiprocessing.Value('d', main_shared_param[key])})

    # Allocate and Initialize shared memory (Main Data Buffer)
    shape = options.get_shape(model)
    memory_size = int(np.prod(shape) * np.dtype(options.dtype).itemsize)
    shared_mem = shm.SharedMemory(create=True, size=memory_size)
    shared_buffer = np.ndarray(shape, dtype=options.dtype, buffer=shared_mem.buf)
    shared_buffer[:] = np.nan
    memory_names = [shared_mem.name]

    # Allocate and Initialize shared memory (Thermodynamic Plot Data Buffer)
    if options.draw_thermo_plot:
        thermo_shape = options.get_thermo_shape(model)
        memory_size = int(np.prod(thermo_shape) * np.dtype(options.dtype).itemsize)
        thermo_mem = shm.SharedMemory(create=True, size=memory_size)
        thermo_buffer = np.ndarray(thermo_shape, dtype=options.dtype, buffer=thermo_mem.buf)
        thermo_buffer[:] = np.nan
        memory_names.append(thermo_mem.name)

    # Start the calculation process
    calc_process = multiprocessing.Process(target=worker, args=(model, options, memory_names, stop_flag, shared_params))
    calc_process.start()

    dashboard_process = multiprocessing.Process(target=plot_dashboard, args=(shared_params, stop_flag, options))
    dashboard_process.start()

    # Start the plotting process
    plot_process = multiprocessing.Process(target=plot_results, args=(model, options, memory_names, stop_flag))
    plot_process.start()

    if options.draw_thermo_plot:
        thermo_plot_process = multiprocessing.Process(target=plot_thermo_plot, args=(model, options, memory_names, stop_flag))
        thermo_plot_process.start()

    # Start keyboard input monitoring process
    keyboard_listener(model, stop_flag, shared_params)

    # Wait for the workers to finish
    calc_process.join()
    plot_process.join()
    dashboard_process.join()

    if options.draw_thermo_plot:
        thermo_plot_process.join()
