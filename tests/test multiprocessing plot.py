import multiprocessing.shared_memory as shm
from multiprocessing import Manager
import matplotlib.pyplot as plt
from pynput import keyboard
import multiprocessing
import numpy as np
import time


# Global variables for timestep and frequency
time_factor = 50.               # time Acceleration Factor
calculation_frequency = 1000     # Calculation frequency (Hz)
plot_frequency = 30              # plot update frequency (Hz)
buffer_fill_in = 10              # Buffer Filling Time (s)

buffer_size = int(buffer_fill_in * calculation_frequency / time_factor)
dtype = np.float64  # Data type
shape = (buffer_size, 3)

m_in_max = 100                  # Maximum flow rate [kg/s]

# Define constants
g = 9.81        # Gravity [m/s^2]
rho = 1000      # Density [kg/m^3]
a_out = 0.1     # Outflow area [m^2]
a_int = 10      # Cross-sectional area of tank [m^2]


# Worker function for the parallel computation
def worker(stop_flag, shared_name, m_in_perc):

    """Worker function for each calculation step."""
    t = 0  # Starting time
    h = 0  # Starting height

    buffer_head = 0
    global m_in_max  # Access global flow rate variables
    existing_shm = shm.SharedMemory(name=shared_name)
    buffer_arr = np.ndarray(shape, dtype=dtype, buffer=existing_shm.buf)

    mean_sleep_time = 0.
    count = 0.
    while not stop_flag.is_set():

        start_time = time.time()

        # Perform your calculation step
        v_out = np.sqrt(2 * g * h)
        m_out = rho * v_out * a_out
        dt = time_factor / calculation_frequency

        # Use the dynamically adjusted flow rate (percentage of m_in_max)
        m_in = (m_in_perc.value / 100) * m_in_max

        t = t + dt
        h = h + (m_in - m_out) * dt / (rho * a_int)

        # Update shared data (buffer)
        buffer_arr[buffer_head, :] = np.array([t, h, m_in])
        buffer_head = np.mod(buffer_head + 1, buffer_size)

        # Calculate the time taken for the current step
        t_sleep_max = 1 / calculation_frequency
        elapsed_time = time.time() - start_time
        sleep_time = max(0., t_sleep_max - elapsed_time)  # Sleep to ensure dt time step
        mean_sleep_time += sleep_time / t_sleep_max
        count += 1

        time.sleep(sleep_time)  # Sleep for the remainder of the timeste

    mean_sleep_time = mean_sleep_time / count
    occupation = 1 - mean_sleep_time
    print(

        "Worker finished! (mean sleep time {:.2f}ms, cycle occupation: {:.2f}%, iterations: {})".format(
            mean_sleep_time * t_sleep_max * 1000,
            occupation * 100,
            count

        )

    )


# Plotting function
def plot_results(stop_flag, shared_name):
    """Real-time plotting of results."""

    plt.ion()  # Turn on interactive mode
    fig, axs = plt.subplots(nrows=2)

    existing_shm = shm.SharedMemory(name=shared_name)
    buffer_arr = np.ndarray(shape, dtype=dtype, buffer=existing_shm.buf)
    mean_sleep_time = 0.
    count = 0.

    while not stop_flag.is_set():

        start_time = time.time()
        sorted_indices = np.argsort(np.nan_to_num(buffer_arr[:, 0], nan=np.inf))
        sorted_buffer = buffer_arr[sorted_indices]

        for n, ax in enumerate(axs):
            ax.clear()
            ax.plot(sorted_buffer[:, 0], sorted_buffer[:, n+1])
            ax.set_xlabel('Time (s)')

        axs[0].set_ylabel('Height (m)')
        axs[1].set_ylabel('flow rate (kg/s)')
        plt.draw()

        t_sleep_max = 1 / plot_frequency
        elapsed_time = time.time() - start_time
        sleep_time = max(0., t_sleep_max - elapsed_time)  # Sleep to ensure dt time step

        mean_sleep_time += sleep_time / t_sleep_max
        count += 1

        plt.pause(sleep_time)  # Small pause to allow updates

    plt.ioff()
    mean_sleep_time = mean_sleep_time / count
    occupation = 1 - mean_sleep_time
    print(

        "Plotter finished! (mean sleep time {:.2f}ms, cycle occupation: {:.2f}%, iterations: {})".format(
            mean_sleep_time * t_sleep_max * 1000,
            occupation * 100,
            count

        )

    )


# Keyboard input monitoring function
def listen_for_esc(stop_flag, m_in_perc):
    with keyboard.Listener(on_press=lambda key: stop_processes(key, stop_flag, m_in_perc)) as listener:
        listener.join()

    print("Listener finished!")

def stop_processes(key, stop_flag, m_in_perc):

    if key == keyboard.Key.esc:
        print("Esc pressed! Terminating all processes...")
        stop_flag.set()
        return False

    elif key == keyboard.Key.up:
        # Increase flow rate by 1% up to 100%
        if m_in_perc.value < 100:
            m_in_perc.value += 1.

    elif key == keyboard.Key.down:
        # Decrease flow rate by 1% down to 0%
        if m_in_perc.value > 0:
            m_in_perc.value -= 1

    return True

def run_simulation():

    manager = Manager()
    stop_flag = manager.Event()
    m_in_perc = multiprocessing.Value('d', 50.)

    # Initialize shared data (buffer)
    shared_mem = shm.SharedMemory(create=True, size=int(np.prod(shape) * np.dtype(dtype).itemsize))
    shared_buffer = np.ndarray(shape, dtype=dtype, buffer=shared_mem.buf)
    shared_buffer[:] = np.nan

    # Start the calculation process
    calc_process = multiprocessing.Process(target=worker, args=(stop_flag, shared_mem.name, m_in_perc))
    calc_process.start()

    # Start the plotting process
    plot_process = multiprocessing.Process(target=plot_results, args=(stop_flag, shared_mem.name))
    plot_process.start()

    # Start keyboard input monitoring process
    listen_for_esc(stop_flag, m_in_perc)

    # Wait for the workers to finish
    calc_process.join()
    plot_process.join()


if __name__ == "__main__":
    run_simulation()
