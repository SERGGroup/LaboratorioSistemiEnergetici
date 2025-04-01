from multiprocessing import Manager
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
from keyboardMac import is_pressed
import time

# Global variables for timestep and frequency
time_factor = 10.               # time Acceleration Factor
calculation_frequency = 10000   # Calculation frequency (Hz)
plot_frequency = 10             # plot update frequency (Hz)
buffer_fill_in = 10             # Buffer Filling Time (s)

buffer_size = int(buffer_fill_in * calculation_frequency)
buffer = np.array((buffer_size, 2))
buffer[:] = np.nan

m_in_percentage = 50            # Initial flow rate as a percentage (50% of m_in_max)
m_in_max = 100                  # Maximum flow rate [kg/s]

# Define constants
g = 9.81  # Gravity [m/s^2]
rho = 1000  # Density [kg/m^3]
a_out = 1.0  # Outflow area [m^2]
a_int = 10  # Cross-sectional area of tank [m^2]


# Worker function for the parallel computation
def worker(stop_flag):

    """Worker function for each calculation step."""
    t = 0  # Starting time
    h = 0  # Starting height

    buffer_head = 0
    global m_in_percentage, m_in_max, buffer, buffer_size  # Access global flow rate variables

    while not stop_flag.is_set():

        start_time = time.time()

        # Perform your calculation step
        v_out = np.sqrt(2 * g * h)
        m_out = rho * v_out * a_out
        dt = time_factor / calculation_frequency

        # Use the dynamically adjusted flow rate (percentage of m_in_max)
        m_in = (m_in_percentage / 100) * m_in_max

        t = t + dt
        h = h + (m_in - m_out) * dt / (rho * a_int)

        # Update shared data (buffer)
        buffer[buffer_head, :] = np.array(t, h)
        buffer_head = np.mod(buffer_head + 1, buffer_size)

        # Calculate the time taken for the current step
        t_sleep_max = 1 / calculation_frequency
        elapsed_time = time.time() - start_time
        sleep_time = max(0., t_sleep_max - elapsed_time)  # Sleep to ensure dt time step
        time.sleep(sleep_time)  # Sleep for the remainder of the timestep


# Plotting function
def plot_results(stop_flag):
    """Real-time plotting of results."""

    plt.ion()  # Turn on interactive mode
    fig, ax = plt.subplots()
    global buffer

    while not stop_flag.is_set():

        ax.clear()

        ax.scatter(buffer[:, 0], buffer[:, 1], marker='o')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Height (m)')
        ax.set_title('Real-Time Tank Level')
        plt.draw()

        plt.pause(1/plot_frequency)  # Small pause to allow updates

    plt.ioff()
    plt.show()


# # Keyboard input monitoring function
# def keyboard_input(stop_flag):
#     """Monitor the keyboard for up/down arrow key presses to adjust flow rate."""
#     global m_in_percentage
#
#     while not stop_flag.is_set():
#
#         if is_pressed('up'):
#             # Increase flow rate by 1% up to 100%
#             if m_in_percentage < 100:
#                 m_in_percentage += 1
#
#         elif is_pressed('down'):
#             # Decrease flow rate by 1% down to 0%
#             if m_in_percentage > 0:
#                 m_in_percentage -= 1
#
#         time.sleep(0.1)  # Delay to avoid spamming the key press


def run_simulation():
    # Initialize shared data (buffer)
    manager = Manager()
    stop_flag = manager.Event()

    # Start the calculation process
    calc_process = multiprocessing.Process(target=plot_results, args=stop_flag)
    calc_process.start()

    # Start the plotting process
    plot_process = multiprocessing.Process(target=plot_results, args=stop_flag)
    plot_process.start()

    # Start keyboard input monitoring process
    # input_process = multiprocessing.Process(target=keyboard_input, args=(stop_flag,))
    # input_process.start()

    # Wait for the workers to finish
    calc_process.join()

    stop_flag.set()  # Stop the plotting and keyboard processes
    plot_process.join()
    # input_process.join()


if __name__ == "__main__":
    run_simulation()
