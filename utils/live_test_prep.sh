#!/bin/bash

sudo apt-get install virtualenv python3-venv
python3 -m venv /tmp/myproject
source /tmp/myproject/bin/activate
pip install timeout-decorator 
pip install -r requirements.txt
source /tmp/myproject/bin/activate
