# Apigee API Platform Tools

This project contains tools for the Apigee Gateway Services platform. It is
a Python project that contains tools to:

* Deploy API proxies
* Create skeleton proxies
* Deploy Node.js applications

## Installation

These tools are a Python package like many others. To install them, run:

    python setup.py install
    
On a Mac or Linux you may have to use `sudo` to run this so that the tools
are installed in a system directory like `/usr/local/bin`, like this:

    sudo python setup.py install
    
## Usage

`setup.py` installs one tool called `apigeetool`. Run `apigeetool` to see the
list of commands that it supports.
