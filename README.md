# ConnectionKeepAlive
Python Solution to test, track, and keep alive ISP connection.

## Prerequisites ##

`Python` and `pip` must be installed on your system and they must be of the same 2.x version. To check:

    $ pip --version
    pip 9.0.1 from /usr/local/lib/python2.7/site-packages (python 2.7)
    $ python --version
    Python 2.7.12

## Installation ##

1. Clone this repository.
2. Go to the project folder and install its dependencies:
`pip install -r requirements.txt`

## Running ##

    python watcher.py http://10.160.0.1/login <login>

The tool will ask for a connection password and start monitoring. Logs are written to stdout.
