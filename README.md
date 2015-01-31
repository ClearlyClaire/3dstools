Collection of stupid scripts to ease reverse engineering of 3DS applications
============================================================================

* launcher.py generates a Launcher.dat file that can dump ~6.7MiB of the
  current application's RAM
* findtext.py tries to find the address of the .text in a memory dump
* findgspinterrupt.py tries to find the address of a GSP interrupt table
  from a memory dump
* findservices.py tries to automatically find service handles in a memory dump
