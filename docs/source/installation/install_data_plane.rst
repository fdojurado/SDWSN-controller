=====================
Set up the data plane
=====================

The data plane adopts the Contiki-NG_ operating system, but we have modified it to support new functionalities.

Installation instructions
-------------------------
The same installation instructions of Contiki-NG_ apply here. Information on supported platforms, networking modules, storage systems, tutorials, etc. can be found on the `Contiki-NG website <https://www.contiki-ng.org/>`_.

Cooja simulation
^^^^^^^^^^^^^^^^^^^^^
We currently support Docker_. Installation instructions can be found in `here <https://github.com/contiki-ng/contiki-ng/wiki/Docker>`_. \
Remember to create an alias for your Contiki-NG (e.g. contiker).

Real-world deployment
^^^^^^^^^^^^^^^^^^^^^
You just need to compile your code and upload your firmware to your device.

.. _Contiki-NG: https://github.com/contiki-ng/contiki-ng
.. _Docker: https://www.docker.com/