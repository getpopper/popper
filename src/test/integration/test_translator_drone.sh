#!/bin/bash

marker="POPPER-DRONE-TRANSLATION"
filename="out.txt"

# create and cd into a workspace
tmp_dir=$(mktemp -d)
cd $tmp_dir

# create a popper workflow
cat << EOT >> wf.yml
steps:
  - runs:
    uses: docker://alpine
    runs:
      [/bin/sh]
    args: [-c, 'echo $marker > $filename']
EOT

# clean the output
rm -f $filename

# translate the workflow
popper translate -f wf.yml

# execute the workflow with Drone and check the result
drone exec
if ! cat ./$filename | grep -q $marker; then
  >&2 echo "Failed to find the marker in the drone output"
  exit 1
fi

echo "Drone generated a correct file from the translated workflow"
exit 0
