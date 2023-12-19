#!/bin/bash

# # First run 
# rm -rf /tmp/myproject
# sudo apt-get install virtualenv python3-venv
# python3 -m venv /tmp/myproject
# source /tmp/myproject/bin/activate
# pip install google-api-python-client
# pip install google-auth-oauthlib
# pip install pytest

#Subsequent runs 
python3 -m venv /tmp/myproject
source /tmp/myproject/bin/activate
python3 google_api_client_test.py
python3 migration_util_change_client_test.py
python3 gbra_migration_util_test.py
python3 google_api_client_test.py
