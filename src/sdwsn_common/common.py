""" This python script holds common functions used across the controller """
import multiprocessing as mp
from sdwsn_serial import serial
import networkx as nx
import numpy as np
from sdwsn_database.database import NODES_INFO


def build_link_schedules_matrix_obs(packet_dissector, mySchedule):
    print("building link schedules matrix")
    # Get last index of sensor
    N = packet_dissector.get_last_index_wsn()+1
    # This is an array of schedule matrices
    link_schedules_matrix = [None] * N
    # Last timeslot offset of the current schedule
    last_ts = 0
    # We now loop through the entire array and fill it with the schedule information
    for node in mySchedule.list_nodes:
        # Construct the schedule matrix
        schedule = np.zeros(
            shape=(mySchedule.num_channel_offsets, mySchedule.slotframe_size))
        for rx_cell in node.rx:
            # print("node is listening in ts " +
            #       str(rx_cell.timeoffset)+" ch "+str(rx_cell.channeloffset))
            schedule[rx_cell.channeloffset][rx_cell.timeoffset] = 1
            if rx_cell.timeoffset > last_ts:
                last_ts = rx_cell.timeoffset
        for tx_cell in node.tx:
            # print("node is transmitting in ts " +
            #       str(tx_cell.timeoffset)+" ch "+str(tx_cell.channeloffset))
            schedule[tx_cell.channeloffset][tx_cell.timeoffset] = -1
            if tx_cell.timeoffset > last_ts:
                last_ts = tx_cell.timeoffset
        addr = node.node.split(".")
        link_schedules_matrix[int(
            addr[0])] = schedule.flatten().tolist()
    # print("link_schedules_matrix")
    # print(link_schedules_matrix)
    # using list comprehension
    # to remove None values in list
    res = [i for i in link_schedules_matrix if i]
    # Save in DB
    # current_time = datetime.now().timestamp() * 1000.0
    # data = {
    #     "timestamp": current_time,
    #     "schedules": res
    # }
    # Database.insert(SCHEDULES, data)
    return res, last_ts



def compute_algo(G, alg, routes):
    # We first make sure the G is not empty
    if(nx.is_empty(G) == False):
        if(G.has_node(1)):  # Maybe use "1.0" instead
            print("graph has the controller")
            routes.clear_routes()
            match alg:
                case "dijkstra":
                    print("running dijkstra")
                    path = dijkstra(G, routes)
                case "mst":
                    print("running MST")
                    path = mst(G)
    else:
        print("not able to compute routing, graph empty")
    return path


""" Coprime checks methods """

# These are the size of other schedules in orchestra
eb_size = 397
common_size = 31
control_plane_size = 27


def gcd(p, q):
    # Create the gcd of two positive integers.
    while q != 0:
        p, q = q, p % q
    return p


def fc_is_coprime(x, y):
    return gcd(x, y) == 1


def compare_coprime(num):
    sf_sizes = [eb_size, common_size, control_plane_size]
    result = 0
    for sf_size in sf_sizes:
        is_coprime = fc_is_coprime(num, sf_size)
        result += is_coprime

    if result == 3:
        return 1
    else:
        return 0


def next_coprime(num):
    is_coprime = 0
    while not is_coprime:
        num += 1
        # Check if num is coprime with all other sf sizes
        is_coprime = compare_coprime(num)
    print(f'next coprime found {num}')
    return num


def previous_coprime(num):
    is_coprime = 0
    while not is_coprime:
        num -= 1
        # Check if num is coprime with all other sf sizes
        is_coprime = compare_coprime(num)
    print(f'previous coprime found {num}')
    return num
