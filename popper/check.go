package main

import (
	"fmt"
	"io/ioutil"
	"log"
	"strings"

	sh "github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

var environment []string
var volumes []string
var skip string
var checksh = `#!/bin/bash
set -e
type docker >/dev/null 2>&1 || { echo >&2 "Can't find docker command."; exit 1; }

docker_path=""

if [ $OSTYPE == "linux-gnu" ] ; then
  docker_path=$(which docker)
  libltdl_path=$(ldd $docker_path | grep libltdl | awk '{print $3}')
	if [ -n "$libltdl_path" ] ; then
    libltdl_path="--volume $libltdl_path:/usr/lib/$(basename $libltdl_path)"
	fi
elif  [[ $OSTYPE == *"darwin"* ]]; then
  docker_path="/usr/bin/docker"
  libltdl_path=""
else
  echo "Unrecognized OS: $OSTYPE"
  exit 1
fi

echo "Starting Popper check"
docker pull ivotron/popperci-experimenter &> /dev/null
docker run --rm %s \
  $libltdl_path \
  --volume $PWD:$PWD \
  --volume $docker_path:/usr/bin/docker \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  --workdir $PWD \
  ivotron/popperci-experimenter %s
`

func writePopperCheckScript() {
	env := ""
	if len(environment) > 0 {
		env += " -e " + strings.Join(environment, " -e ")
	}
	if len(volumes) > 0 {
		env += " -v " + strings.Join(volumes, " -v ")
	}
	content := fmt.Sprintf(checksh, env, "--skip "+skip)
	err := ioutil.WriteFile("/tmp/poppercheck", []byte(content), 0755)
	if err != nil {
		log.Fatalln("Error writing bash script to /tmp")
	}
}

var checkCmd = &cobra.Command{
	Use:   "check",
	Short: "Check integrity of an experiment",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		writePopperCheckScript()
		if err := sh.Command("/tmp/poppercheck").Run(); err != nil {
			log.Fatalln(err)
		}
	},
}

func init() {
	RootCmd.AddCommand(checkCmd)

	checkCmd.Flags().StringSliceVarP(&environment, "environment", "e", []string{}, "Environment variables to be defined inside the test container.")
	checkCmd.Flags().StringSliceVarP(&volumes, "volume", "v", []string{}, "Volumes to be passed to the test container.")
	checkCmd.Flags().StringVarP(&skip, "skip", "s", "", "Comma-separated list of stages to skip.")
}
