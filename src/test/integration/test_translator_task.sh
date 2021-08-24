#!/bin/bash
set -ex

if [[ -z $ENABLE_TASK_TRANSLATOR_TESTS ]]; then
  exit 0
fi

marker="POPPER-TASK-TRANSLATION"
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
popper translate -f wf.yml --to task

# execute the workflow with Drone and check the result
task
if ! cat ./$filename | grep -q $marker; then
  >&2 echo "Failed to find the marker in the task output"
  exit 1
fi

echo "Task generated a correct file from the translated workflow"
exit 0
