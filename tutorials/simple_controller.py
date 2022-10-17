from sdwsn_controller.controller.container_controller import ContainerController
from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler
from sdwsn_controller.routes.dijkstra import Dijkstra
import sys


def data_plane_initial_setup(controller):
    controller.reset()
    # We now wait until we reach the processing_window
    controller.wait()
    # We get the network links, useful when calculating the routing
    G = controller.get_network_links()
    # Run the dijkstra algorithm with the current links
    path = controller.compute_routes(G)
    # Set the slotframe size - (Max # of sensor in WSN is 10)
    slotframe_size = 12
    # We now set the TSCH schedules for the current routing
    controller.compute_tsch_schedule(path, slotframe_size)
    # Send the entire routes
    controller.send_routes()
    # Send the entire TSCH schedule
    controller.send_tsch_schedules()
    # Delete the current nodes_info collection from the database
    controller.delete_info_collection()
    controller.reset_pkt_sequence()
    # Wait for the network to settle
    controller.wait()


def main():

    # Script that run inside the container - simulation file as argument
    run_simulation_file = '/bin/sh -c '+'"cd ' + \
        'examples/elise'+' && ./run-cooja.py cooja-orchestra.csc"'

    # TSCH scheduler
    tsch_scheduler = ContentionFreeScheduler()

    # Routing algorithm
    routing = Dijkstra()

    controller = ContainerController(
        image='contiker/contiki-ng',
        command=run_simulation_file,
        target='/home/user/contiki-ng',
        source='/Users/ffjla/ELISE/contiki-ng',
        socket_file='/Users/ffjla/ELISE/contiki-ng' +
        '/'+'examples/elise'+'/'+'COOJA.log',
        db_name='mySDN',
        db_host='127.0.0.1',
        db_port=27017,
        processing_window=200,
        router=routing,
        tsch_scheduler=tsch_scheduler
    )

    # Let's start the data plane first
    data_plane_initial_setup(controller)


if __name__ == '__main__':
    main()
    sys.exit(0)
