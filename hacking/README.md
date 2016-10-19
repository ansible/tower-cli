'Hacking' directory tools
=========================

Env-setup
---------

The 'env-setup' script modifies your environment to allow you to run
tower-cli from a git checkout using python 2.6+.

First, set up your environment to run from the checkout:

    $ source ./hacking/env-setup

You will need some basic prerequisites installed.  If you do not already have them
and do not wish to install them from your operating system package manager, you
can install them from pip

    $ easy_install pip               # if pip is not already available
    $ pip install -r requirements.txt

From there, follow tower-cli instructions on docs.ansible.com as normal.


