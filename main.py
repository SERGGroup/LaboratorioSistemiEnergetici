# %% IMPORT LIBRARIES
import matplotlib.pyplot as plt
import numpy as np


# %%
t = 0
h = 3       # m
int_dh = 0.
dh_old = None
times = list()
heights = list()
params = list()


# %%
dt = 0.1      # s

g = 9.81    # m / s
rho = 1000  # kg / m ^ 3
d = 0.01    # m
D = 1       # m

a_out = np.pi * d ** 2 / 4
a_int = np.pi * D ** 2 / 4

t_max = 22*3600

k_p = 2.        # (kg/s)/m
k_i = 0.001     # (kg/s)/(m*s)
k_d = 0.

h_target = 12.5   # m

int_dh_max = 2000.
m_in_des = 1   # kg/s
m_in_max = m_in_des * 2

while t < t_max:

    t = t + dt
    v_out = np.sqrt(2 * g * h)
    m_out = rho * v_out * a_out

    dh_curr = h_target - h

    if dh_old is None:
        der_dh = 0.

    else:
        der_dh = (dh_curr - dh_old) / dt

    dh_old = dh_curr
    int_dh = max(min(int_dh + dh_curr * dt, int_dh_max), -int_dh_max)
    m_in_theory = k_p * dh_curr + k_i * int_dh + k_d * der_dh
    m_in = max(min(m_in_theory, m_in_max), 0.)

    h = h + (m_in - m_out) * dt / (rho * a_int)

    times.append(t)
    heights.append(h)
    params.append([v_out, m_out, dh_curr, int_dh, der_dh, m_in, m_in_theory])


# %%
plt.plot(times, heights)
plt.xlim((0., 80000))
plt.show()


# %%
params = np.array(params)
plt.plot(times, params[:, 5:7])
plt.ylim((-0.25, 2.25))
plt.xlim((0., 80000))
plt.show()

# %%
plt.plot(times, params[:, 4])
plt.ylim((-0.005, 0.005))
plt.xlim((0., 80000))
plt.show()
