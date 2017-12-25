package main

import (
	"fmt"
	"log"
	"os"
	"strings"

	sh "github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
	"github.com/theherk/viper"
)

var environment []string
var volume []string
var skip string
var timeout string

func runOnHost(checkFlags []string) {
	s := make([]interface{}, len(checkFlags))
	for i, v := range checkFlags {
		s[i] = v
	}
	if err := sh.Command(popperFolder+"/popper/_check/check.py", s...).Run(); err != nil {
		log.Fatalln(err)
	}
}

func runInDocker(checkFlags []string, checkEnv string) {
	dockerFlags := ""
	if len(environment) > 0 {
		dockerFlags += " -e " + strings.Join(environment, " -e ")
	}
	if len(volume) > 0 {
		dockerFlags += " -v " + strings.Join(volume, " -v ")
	}
	cmd_args := []string{"run", "--rm", "-i"}
	cmd_args = append(cmd_args, strings.Fields(dockerFlags)...)
	dir, err := os.Getwd()
	if err != nil {
		log.Fatal(err)
	}
	cmd_args = append(cmd_args, "--volume", dir+":"+dir, "--workdir", dir, "--volume", "/var/run/docker.sock:/var/run/docker.sock", "falsifiable/poppercheck:"+checkEnv)

	s := make([]interface{}, len(cmd_args)+len(checkFlags))
	for i, v := range cmd_args {
		s[i] = v
	}
	for i, v := range checkFlags {
		s[i+len(cmd_args)] = v
	}
	if err := sh.Command("docker", s...).Run(); err != nil {
		log.Fatalln(err)
	}
}

func runCheck() {
	expName, err := getPipelineName()
	if err != nil {
		log.Fatalln(err)
	}
	err = readPopperConfig()
	if err != nil {
		log.Fatalln(err)
	}

	checkEnv := ""
	if !viper.IsSet("envs." + expName) {
		fmt.Println("No environment in .popper.yml, using host")
		checkEnv = "host"
	} else {
		checkEnv = viper.GetString("envs." + expName)
	}

	checkFlags := []string{"--timeout=" + timeout}
	if len(skip) > 0 {
		checkFlags = append(checkFlags, "--skip="+skip)
	}

	if checkEnv == "host" {
		runOnHost(checkFlags)
	} else {
		runInDocker(checkFlags, checkEnv)
	}
}

var checkCmd = &cobra.Command{
	Use:   "check",
	Short: "Run pipeline and report on its status",
	Long: `Executes an pipeline in its corresponding environment (host or docker). If using docker,
environment variables and folders can be made available inside the container by using -e
and -v flags respectively. These flags are passed down to the 'docker run' command. The
pipeline folder is bind-mounted. If the environment is 'host', the -v and -e flags are
ignored.`,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 0 {
			log.Fatalln("This command doesn't take arguments.")
		}
		initPopperFolder()
		runCheck()
	},
}

func init() {
	RootCmd.AddCommand(checkCmd)

	checkCmd.Flags().StringSliceVarP(&environment, "environment", "e", []string{}, `Environment variable available to the pipeline. Can be
                            given multiple times. This flag is ignored when the environment
                            is 'host'.`)
	checkCmd.Flags().StringSliceVarP(&volume, "volume", "v", []string{}, `Volume available to the pipeline. Can be given multiple times
                            This flag is ignored when the environment is 'host'.`)
	checkCmd.Flags().StringVarP(&skip, "skip", "s", "", "Comma-separated list of stages to skip.")
	checkCmd.Flags().StringVarP(&timeout, "timeout", "t", "36000", "Timeout limit for pipeline in seconds.")
}
