=====================
Set up the data plane
=====================

The data plane adopts the Contiki-NG_ operating system, but we have modified it to support new functionalities.

Installation instructions
-------------------------

You first need to clone the Contiki-NG-SDWSN_ repository.

    .. code-block:: console

        $ git clone https://github.com/fdojurado/contiki-ng

The same installation instructions of Contiki-NG_ apply here. Information on supported platforms, networking modules, storage systems, tutorials, etc. can be found on the `Contiki-NG website <https://www.contiki-ng.org/>`_.

Cooja simulation
^^^^^^^^^^^^^^^^^^^^^
We currently support native simulation on the host or Docker_. Installation instructions to run it on Docker can be found in `here <https://docs.contiki-ng.org/en/develop/doc/getting-started/Docker.html>`_. \
Remember to create an alias for your Contiki-NG (e.g. contiker).

Real-world deployment
^^^^^^^^^^^^^^^^^^^^^
You just need to compile your code and upload your firmware to your device.

.. _Contiki-NG-SDWSN: https://github.com/fdojurado/contiki-ng
.. _Contiki-NG: https://docs.contiki-ng.org/en/develop/
.. _Docker: https://www.docker.com/