Help to install xtb module
============================


Download the official binary
----------------------

Follow these steps:

.. code-block:: shell
    
    mkdir ~/tools/xtb
    cd ~/tools/xtb
    wget https://github.com/grimme-lab/xtb/releases/download/v6.6.0/xtb-6.6.0-linux-x86_64.tar.xz
    

Extract it
-----------------------

Make the following modification to the source code:

.. code-block:: shell

    tar -xf xtb-6.6.0-linux-x86_64.tar.xz


Add to PATH
---------------------------

Optional but convenient (if you use bash):

.. code-block:: shell

    echo 'export PATH=$HOME/programs/xtb/xtb-6.6.0/bin:$PATH' >> ~/.bashrc
    source ~/.bashrc


Sanity check
---------------------------

Check to see if it is succesfully installed:

.. code-block:: shell

    which xtb

