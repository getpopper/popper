#!/bin/bash

# Clone and start the server
python -m virtualenv /tmp/popper-badge-server
git clone https://github.com/popperized/popper-badge-server.git ~/tmp/popper-badge-server/src
source /tmp/popper-badge-server/bin/activate
pip install -r /tmp/popper-badge-server/src/requirements.txt
python /tmp/popper-badge-server/src/app.py &
deactivate

# Use popper run to test the badge server
source common-setup.sh
init_test
sed -i '$s/.*/badge-server-url: http:\/\/127.0.0.1:5000/' .popper.yml
popper init mypipeone
git remote add origin https://github.com/systemslab/popper.git
git add .
git commit -m "Add mypipeone"
popper run
git remote remove origin

# Kill the server and clean up
set -ex
ps -ef | grep "app.py" | awk '{print $2}' | xargs kill
rm -rf /tmp/popper-badge-server
