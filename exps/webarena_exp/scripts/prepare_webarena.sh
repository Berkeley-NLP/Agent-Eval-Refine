#!/bin/bash

SERVER="localhost"

# Export the environmental variables
export SHOPPING=http://${SERVER}:7770
export SHOPPING_ADMIN=http://${SERVER}:7780/admin
export REDDIT=http://${SERVER}:9999
export GITLAB=http://${SERVER}:8023
export MAP=http://miniserver1875.asuscomm.com:3000
export WIKIPEDIA=http://${SERVER}:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing
export HOMEPAGE=http://${SERVER}:4399

# Generate config file for each test example
python scripts/generate_test_data.py

# Obtain the auto-login cookies for all websites
mkdir -p ./.auth
python browser_env/auto_login.py