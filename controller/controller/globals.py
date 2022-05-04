import numpy as np

# routes_matrix, nbr_rssi_matrix, nbr_etx_matrix


def globals_initialize():
    print("initializing globals")
    global routes_matrix, nbr_rssi_matrix, nbr_etx_matrix, link_schedules_matrix
    routes_matrix = np.array([])
    nbr_rssi_matrix = np.array([])
    nbr_etx_matrix = np.array([])
    link_schedules_matrix = np.array([])
