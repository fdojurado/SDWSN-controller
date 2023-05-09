========================
Set up the control plane
========================

In its core runs Python_, the repository can be found in SDWSN-Controller_.

Control plane Requirements
--------------------------
* Python_ 3.10 or newer
* Docker_ (Docker Engine)
* NumPy_ (base N-dimensional array package)
* Pandas_ (library for data manipulation and analysis)
* stable_baselines3_ (For reinforcement learning)
* python-daemon_ (daemon process)
* networkx_ (manipulation of complex networks)
* pip-docker_ (Docker SDK for Python)


Installing the controller
-------------------------

.. highlight:: bash

Install
=======

Before jumping into the following steps, you at least need to install Python_, and Docker_ (For Cooja simulations).

Then, install the package, execute the below commands.

#. Clone the repository.

    .. code-block:: console

        $ git clone https://github.com/fdojurado/SDWSN-controller.git

#. You may want to create a virtual environment, in the repository folder run.

    .. code-block:: console

        $ python -m venv venv

#. Activate the virtual environment.

    .. code-block:: console

        $ source venv/bin/activate

#. In the repository folder run.

    .. code-block:: console

        $ python -m pip install .

Run under development
=====================

You may want to run the package in development mode by.

.. code-block:: console

    $ python -m pip install -e .


Verify control plane installation
==================================
You can verify the installation of the control plane by running.

.. code-block:: console

    $ python -m pip list

You should be able to see the package ``sdwsn-controller`` in the list.

Running the data plane in Cooja
-------------------------------

If you want to run the data plane in the Cooja network simulator, you first need to setup your data plane by following the instructions in :ref:`here<Set up the data plane>`.

.. If you want to run Cooja with the GUI follow the below instructions.


.. Cooja (GUI) using "Docker for Mac"
.. ==================================
.. Docker for Mac can be installed following the instructions in `here <https://docs.docker.com/docker-for-mac/>`_.

.. If you want to run the control plane in your computer environment, but Cooja in Docker then you need to open the port in the docker file, you can do this by adding ``-p 60001:60001`` in your contiker alias.

.. Put the following lines into ``~/.profile`` or similar.

.. ::

..     export CNG_PATH=<absolute-path-to-your-contiki-ng>
..     alias contiker="docker run --privileged \
..     --mount type=bind,source=$CNG_PATH,destination=/home/user/contiki-ng \
..     --sysctl net.ipv6.conf.all.disable_ipv6=0 \
..     -e DISPLAY=docker.for.mac.host.internal:0 \
..     -p 60001:60001 \
..     -ti contiker/contiki-ng"

.. If you run into trouble opening X11 (if you need GUI) display in macOS; `this <https://gist.github.com/cschiewek/246a244ba23da8b9f0e7b11a68bf3285#gistcomment-3477013>`_ has worked for me.

.. Before running the examples run the following command in the Cooja folder of the Contiki-NG-SDWSN repository.

.. ::

..  $ contiker
..  user@xxxx:~/contiki-ng$ cd tools/cooja
..  user@xxxx:~/contiki-ng/tools/cooja$ ant run

.. This command will throw an error if a display has not been set. So, we just skip it as we are not using the GUI.



.. _Python: https://www.python.org/
.. _Docker: https://www.docker.com/
.. _NumPy: https://docs.scipy.org/doc/numpy/reference/
.. _Pandas: https://pandas.pydata.org/docs/reference/index.html
.. _stable_baselines3: https://stable-baselines3.readthedocs.io/en/master/
.. _SDWSN-Controller: https://github.com/fdojurado/SDWSN-controller
.. _python-daemon: https://pypi.org/project/python-daemon/
.. _networkx: https://pypi.org/project/networkx/
.. _pip-docker: https://pypi.org/project/docker/

