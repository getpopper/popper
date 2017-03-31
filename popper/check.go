package main

import (
	"fmt"
	"io/ioutil"
	"log"
	"strings"

	"github.com/spf13/cobra"
)

var environment []string
var volumes []string

var checkSh = []byte(`#!/bin/bash
type docker >/dev/null 2>&1 || { echo >&2 "Can't find docker command."; exit 1; }

docker_path=""

if [ $OSTYPE == "linux-gnu" ] ; then
  docker_path=$(which docker)
  libltdl_path=$(ldd /usr/bin/docker | grep libltdl | awk '{print $3}')
  libltdl_path="--volume $libltdl_path:/usr/lib/$(basename $libltdl_path)"
elif  [[ $OSTYPE == *"darwin"* ]]; then
  docker_path="/usr/bin/docker"
  libltdl_path=""
else
  echo "Unrecognized OS: $OSTYPE"
  exit 1
fi

docker run --rm \
  $@ \
  $libltdl_path \
  --volume $PWD:$PWD \
  --volume /tmp:/tmp \
  --volume $docker_path:/usr/bin/docker \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  --workdir $PWD \
  -e SKIP='/root/clone.sh' \
  ivotron/popperci
`)

var checkCmd = &cobra.Command{
	Use:   "check",
	Short: "Check integrity of an experiment",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		err := ioutil.WriteFile("/tmp/poppercheck", checkSh, 0755)
		if err != nil {
			log.Fatalln("Error writing shell command to /tmp")
		}
		envVols := ""
		if len(environment) > 0 {
			envVols += "-e " + strings.Join(environment, " -e ")
		}
		if len(volumes) > 0 {
			envVols += "-v " + strings.Join(volumes, " -v ")
		}
		fmt.Printf("%v\n", envVols)
		//sh.Command("/tmp/poppercheck " + envVols).Run()

	},
}

func init() {
	RootCmd.AddCommand(checkCmd)

	checkCmd.Flags().StringSliceVarP(&environment, "environment", "e", []string{}, "Environment variables to be defined inside the test container.")
	checkCmd.Flags().StringSliceVarP(&volumes, "volume", "v", []string{}, "Volumes to be passed to the test container.")
}
