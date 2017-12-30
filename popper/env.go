package main

import (
	"fmt"
	"log"
	"strings"

	"github.com/spf13/cobra"
	"github.com/theherk/viper"
)

var availableEnvs = []string{"host", "alpine-3.4", "centos-7.2", "ubuntu-16.04"}

var envCmd = &cobra.Command{
	Use:   "env",
	Short: "Manage environment used by the 'popper check' command.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) == 0 {
			log.Fatalln("This command cannot be used directly. Run 'popper help env'.")
		}
	},
}

var envListCmd = &cobra.Command{
	Use:   "list",
	Short: "Show available environments.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) > 0 {
			log.Fatalln("This command does not take arguments. Run 'popper help env'")
		}
		fmt.Printf("%s\n", strings.Join(availableEnvs, "\n"))
	},
}

var envShowCmd = &cobra.Command{
	Use:   "show [pipeline]",
	Short: "Show environment for a given pipeline.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) > 1 {
			log.Fatalln("This command takes one argument at most. Run 'popper help env'")
		}
		pipelineName := ""
		if len(args) == 0 {
			pipelineName = ensureInPipelineFolder()
		} else {
			ensurePipelineExists(args[0])
			pipelineName = args[0]
		}
		err := readPopperConfig()
		if err != nil {
			log.Fatalln(err)
		}
		if viper.IsSet("envs." + pipelineName) {
			envs := viper.GetStringMapString("envs")
			fmt.Printf("environment: %s\n", envs[pipelineName])
		} else {
			fmt.Println("Cannot find env for pipeline.")
		}
	},
}

var envSetCmd = &cobra.Command{
	Use:   "set [pipeline] env",
	Short: "Set the popper check environment for a pipeline.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) > 2 || len(args) < 1 {
			log.Fatalln("Incorrect number of arguments. Run 'popper help env'.")
		}
		pipelineName := ""
		newCheckEnv := ""
		if len(args) == 1 {
			pipelineName = ensureInPipelineFolder()
			newCheckEnv = args[0]
		} else {
			pipelineName = args[0]
			newCheckEnv = args[1]
		}
		found := false
		for _, v := range availableEnvs {
			if v == newCheckEnv {
				found = true
			}

		}
		if !found {
			log.Fatalln("Environment not supported. See 'popper env list'.")
		}
		err := readPopperConfig()
		if err != nil {
			log.Fatalln(err)
		}
		values := map[string]string{}
		if viper.IsSet("envs") {
			values = viper.GetStringMapString("envs")
		}
		values[pipelineName] = newCheckEnv
		viper.Set("envs", values)

		// add stages
		viper.WriteConfig()

		fmt.Println("Registered '" + newCheckEnv + "' for pipeline '" + pipelineName + "'.")
	},
}

func init() {
	RootCmd.AddCommand(envCmd)
	envCmd.AddCommand(envListCmd)
	envCmd.AddCommand(envShowCmd)
	envCmd.AddCommand(envSetCmd)
}
