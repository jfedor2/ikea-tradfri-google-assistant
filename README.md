# Google Assistant support for IKEA TRADFRI lights #

This is an Actions on Google Smart Home app that allows you to control
IKEA TRADFRI lights through Google Assistant.

It is written in Python using Django and uses the `coap-client` tool
from libcoap to talk to the IKEA gateway.

The `extras` directory contains example configuration files for
deploying the app using nginx and uwsgi, as well as the `action.json`
file that's used to configure the app on Google's side using the
`gactions` command-line tool.

For step-by-step instructions on how to get it to work, see [this
blog post](http://blog.jfedor.org/).
