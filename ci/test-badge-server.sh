#!/bin/bash

# Clone and start the server
python -m virtualenv ~/popper-badge-server
git clone https://github.com/popperized/popper-badge-server.git ~/popper-badge-server/src
source ~/popper-badge-server/bin/activate
pip install -r ~/popper-badge-server/src/requirements.txt
python ~/popper-badge-server/src/app.py &
deactivate

# Use popper run to test the badge server
init_test
sed -i '$s/.*/badge-server-url: http:\/\/127.0.0.1:5000/' .popper.yml
popper init mypipeone
git remote add origin https://github.com/systemslab/popper.git
git add .
git commit -m "Add mypipeone"
popper run

# Kill the server
set -ex
ps -ef | grep "app.py" | awk '{print $2}' | xargs kill
