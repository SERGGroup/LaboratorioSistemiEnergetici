# %% IMPORT MODULES
from main_code import BoilerDynamicModel
from matplotlib import pyplot as plt


# %% STEP
boiler_dynamics = BoilerDynamicModel()
boiler_dynamics.m_dot_in_perc = 0.
boiler_dynamics.yd_perc = 1

times_main = list()
pressures_main = list()
temperatures_main = list()
m_out_main = list()

yds_perc = [0.001, 0.01, 0.1, 1]
for yd_perc in yds_perc:

    boiler_dynamics.V_x = 0.5
    boiler_dynamics.initialize()
    boiler_dynamics.q_in = 1
    boiler_dynamics.yd_perc = yd_perc
    times = list()

    pressures = list()
    temperatures = list()
    v_x = list()

    m_in = list()
    m_out = list()

    for i in range(4000):

        try:
            boiler_dynamics.update(0.05)

            times.append(boiler_dynamics.t)
            pressures.append(boiler_dynamics.P)
            temperatures.append(boiler_dynamics.T)
            v_x.append(boiler_dynamics.V_x)

            m_in.append(boiler_dynamics.m_dot_in)
            m_out.append(boiler_dynamics.m_dot_out)

        except:
            break

    times_main.append(times)
    pressures_main.append(pressures)
    temperatures_main.append(temperatures)
    m_out_main.append(m_out)


# %% PLOT

fig, axs = plt.subplots(nrows=1, ncols=2)

for i, yd_perc in enumerate(yds_perc):
    axs[0].plot(times_main[i][:-1], pressures_main[i][:-1], label=yd_perc)
    axs[1].plot(times_main[i][:-1], m_out_main[i][:-1], label=yd_perc)

plt.legend(loc='best')
plt.show()

