"EVAPORATORE ORC"
import matplotlib.pyplot as plt
from REFPROPConnector import ThermodynamicPoint


#%%  CONDIZIONI INIZIALI
liquido = "n-pentane"

tp = ThermodynamicPoint([liquido], [1.])
tp_liq = ThermodynamicPoint([liquido], [1.])
tp_vap = ThermodynamicPoint([liquido], [1.])

# DATI INIZIALI
T_in = 20
V_in = 1
V_x = 0.5


#   TEMPERATURA INIZIALE
tp.set_variable("T", T_in)


#   CONDIZIONI LIQUIDO SATURO
tp.set_variable("Q", 0)
rho_l = tp.get_variable("rho")
p_sat = tp.get_variable("P")
h_l = tp.get_variable("h")
m_l = rho_l * V_x


#    CONDIZIONI VAPORE SATURO
tp.set_variable("Q", 1)
rho_v = tp.get_variable("rho")
h_v = tp.get_variable("h")
m_v = rho_v * V_in* (1 - V_x)


#    MASSA, TITOLO, ENTALPIA MEDIA A T = T_in
m_tot = m_v + m_l
x = m_v/m_tot
h_tot = h_v * x + h_l * (1-x)

m_tot_iniziale = m_tot


#%% FOR
# CONTENITORI DI INFORMAZIONI
press = []
titoli = []
temperatura = []
enth = []
tempo = []
masse = []


# DATI DI PARTENNZA
h = h_tot
Q_in = 600

t = 0
dt = 1

m_in = 0.3
m_out = 0.2

for i in range(5000): 
    
    if m_tot <= 0:
        break

    # nuove condizioni
    tp.set_variable("H", h)
    tp.set_variable("rho", m_tot / V_in)

    # memorizzo variabili di interesse
    q = tp.get_variable("Q") 
    if 0 <= q <= 1: 
        titoli.append(q)
    else:
        break

    temperatura.append(tp.get_variable("T"))
    enth.append(h)
    press.append(tp.get_variable("P"))
    tempo.append(t)
    masse.append(m_tot)

    # aggiorno variabili
    t += dt
    
    m_tot0 = m_tot
    
    dm = (m_in - m_out) * dt
    m_tot += dm
    
    dh = ((dt * (m_in * h_l - m_out * h_v + Q_in)) - h * dm)/m_tot0
    h += dh
    
    # aggiorno le entalpie a condiz. di vapor saturo e liquido saturo
    tp_liq.set_variable("Q", 0)
    tp_liq.set_variable("P", tp.get_variable("P"))
    
    tp_vap.set_variable("Q", 1)
    tp_vap.set_variable("P", tp.get_variable("P"))
    
    h_l = tp_liq.get_variable("H")
    h_v = tp_vap.get_variable("H")
    

#%% GRAFICI
# === Primo grafico: Titoli ===
plt.figure(figsize=(9, 4.5))
plt.plot(tempo, titoli, color='black', linestyle='-', label='Titoli')
plt.xlabel("Tempo")
plt.ylabel("Valore dei titoli")
plt.title("Andamento dei Titoli nel Tempo")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# === Secondo grafico: Pressione ===
plt.figure(figsize=(9, 4.5))
plt.plot(tempo, press, color='tab:red', linestyle='-', label='Pressione')
plt.xlabel("Tempo")
plt.ylabel("Pressione [Pa]")
plt.title("Evoluzione della Pressione")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# === Terzo grafico: Entalpia ===
plt.figure(figsize=(9, 4.5))
plt.plot(tempo, enth, color='tab:green', linestyle='-', label='Entalpia')
plt.xlabel("Tempo")
plt.ylabel("Entalpia [kJ/kg]")
plt.title("Variazione dell'Entalpia nel Tempo")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# === Quarto grafico: Temperatura ===
plt.figure(figsize=(9, 4.5))
plt.plot(tempo, temperatura, color='tab:orange', linestyle='-', label='Temperatura')
plt.xlabel("Tempo")
plt.ylabel("Temperatura [°C]")
plt.title("Andamento della Temperatura")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

if m_tot != m_tot_iniziale:
    # === Quinto grafico: Massa ===
    plt.figure(figsize=(9, 4.5))
    plt.plot(tempo, masse, color='magenta', linestyle='-', label='Massa')
    plt.xlabel("Tempo")
    plt.ylabel("Massa Kg")
    plt.title("Andamento della Massa")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()



