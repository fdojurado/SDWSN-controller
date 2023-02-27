#!/usr/bin/python3
#
# Copyright (C) 2022  Fernando Jurado-Lasso <ffjla@dtu.dk>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from multiprocessing import Process
# from platform import node
# from unittest import result
from iotlabcli import experiment
import subprocess
from subprocess import Popen, PIPE
from rich.progress import Progress
import iotlabcli
import os
import time
import logging

# Create logger
logger = logging.getLogger(__name__)


def _timeout(start_time, timeout):
    """Return if timeout is reached.

    :param start_time: initial time
    :param timeout: timeout
    :param _now: allow overriding 'now' call
    """
    return time.time() > start_time + timeout


def log_stderr(program: str, line: str) -> None:
    logger.error("%s: %s", program, line.rstrip())


def run_subprocess(args, name, total):
    with Progress(transient=True) as progress:
        progress.add_task(
            "[red]"+name+"...", total=total)
        with Popen(args, stdout=PIPE, stderr=PIPE, shell=True,
                   universal_newlines=True) as proc:
            errs = []
            for line in proc.stderr:
                log_stderr(args[0], line)
                errs.append(line)
            stdout, _ = proc.communicate()
        result = subprocess.CompletedProcess(
            args, proc.returncode, stdout, "\n".join(errs))
    return result


def compile_firmware(firmware_folder, arch_path, firmware_name, app, platform,
                     sdn_orchestra, board, node_id):
    logger.info(f'Building firmware for node id: {node_id}')

    # TODO: For orchestra we need to add the MAKE_WITH_SDN_ORCHESTRA variable

    args = " ".join(["ARCH_PATH="+arch_path, "make -C " +
                    app, "clean TARGET=" + platform])

    result = run_subprocess(args, "Cleaning", None)

    if result.returncode != 0:
        raise Exception("Error executing make clean")

    # compile_command = "ARCH_PATH="+arch_path+" make -C "+app+" TARGET=" + \
    #     platform+" BOARD="+board+" NODE_ID="+node_id + \
    #     " MAKE_WITH_SDN_ORCHESTRA=" + sdn_orchestra

    args = " ".join(["ARCH_PATH="+arch_path, "make -C " +
                    app, "TARGET=" + platform, "BOARD="+board,
                    "NODE_ID="+node_id,
                     "MAKE_WITH_SDN_ORCHESTRA="+sdn_orchestra])

    result = run_subprocess(args, "Compiling", None)

    if result.returncode != 0:
        raise Exception("Error compiling")

    app_folder = os.path.join(app, firmware_name)

    os.replace(app_folder, firmware_folder + "/" + node_id+".iotlab")


def stop_iotlab_exp(api, exp_id):
    """Stops an experiment in the IoT LAB platform

    Args:
        api (Object): API Rest api object
        exp_id (integer): Experiment ID
    """
    logger.info("Stopping experiment %u", exp_id)
    return experiment.stop_experiment(api, exp_id)


def upload_iotlab(args, firmware_dir):

    user, passwd = iotlabcli.get_user_credentials(args.username, args.password)
    api = iotlabcli.Api(user, passwd)

    list_of_nodes = []

    count = 2

    # Adding end nodes firmware and platforms
    for node in args.node_list[1:]:
        node_resource = {"nodes":
                         [
                             'm3-'+node+'.'+args.site+'.iot-lab.info'
                         ],
                         "firmware_path": firmware_dir+'/'+str(count)+'.iotlab'
                         }
        count += 1
        list_of_nodes.append(node_resource)

    # Append controller node
    controller_node = {"nodes":
                       [
                           'm3-'+args.node_list[0]+'.' +
                           args.site+'.iot-lab.info'
                       ],
                       "firmware_path": firmware_dir+'/'+str(1)+'.iotlab'
                       }
    list_of_nodes.append(controller_node)

    resources_config = list_of_nodes
    resources = [experiment.exp_resources(**c) for c in resources_config]
    logger.info('FIT IoT LAB resources needed')
    for resource in resources:
        logging.info((resource))
    exp_res = experiment.submit_experiment(
        api,
        'SDWSN', args.time,
        resources)
    testbed_experiment_id = exp_res["id"]
    # with open("experiment.json", "w") as f:
    #     f.write(json.dumps({"id": testbed_experiment_id}))

    # get the content
    logger.info("Exp submitted with id: %u" % testbed_experiment_id)

    # Wait for the experiment to be in running state
    # wait_exp = experiment.wait_experiment(
    #     api,
    #     testbed_experiment_id
    # )

    with Progress(transient=True) as progress:
        progress.add_task(
            "[red]Waiting for experiment to be in running state...",
            total=None)
        start_time = time.time()
        while not _timeout(start_time, float('+inf')):
            state = experiment.get_experiment(
                api, testbed_experiment_id, '')['state']
            if state in 'Running':
                break
            # Still wait
            time.sleep(5)
    # sleep(60)
    # resetting = iotlabnode.node_command(
    #     api,
    #     'reset',
    #     testbed_experiment_id
    # )
    # logger.info(f"Resetting the entire network: {resetting}")

    return api, testbed_experiment_id


def launch_ssh_tunnel(args):
    """
    Will launch a SSH tunnel. We need it to perform a tunslip on our host.
    """
    target = 'm3-'+args.node_list[0]
    logger.info(
        f"SSH connection to {target} using home port {args.home_port}\
              and target port {args.target_port}")
    # For verbose add -vNT instead
    subprocess.run(["ssh", "-NT",
                    args.username+'@'+args.site+'.iot-lab.info',
                    "-L", "%d:%s:%d" %
                    (args.home_port, target, args.target_port)])


def stop_ssh_tunnel(ssh):
    logger.warning("Shutting down SSH ...")
    ssh.join()


def launch_iotlab(arguments, firmware_dir):
    processes = {
        "upload_iotlab": Process(target=upload_iotlab,
                                 args=(arguments, firmware_dir,)),
        "ssh_tunnel": Process(target=launch_ssh_tunnel, args=(arguments,)),
        # "tunslip": Process(target=launch_tunslip_iotlab),
        # "traffic": Process(target=_gen_traffic),
        # "cache_setup": Process(target=_cache_setup,
        #                       args=(c,)),
        # "reverse_proxy": Process(target=_proxy_cache)
    }
    processes["upload_iotlab"].start()
    processes["upload_iotlab"].join()
    processes["ssh_tunnel"].start()
