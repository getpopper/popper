package main

import (
	"log"

	"github.com/spf13/cobra"
)

var executor string

var initCmd = &cobra.Command{
	Use:   "init",
	Short: "Initializes a popper repository.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 0 {
			log.Fatalln("This command doesn't take arguments.")
		}
		// initManuscript(manuscriptBackend)
		//   options:
		//   - markdown
		//   - latex
		//   - ...
		//
		// initDataOutput(dataOutputBackend)
		//   options:
		//   - csv
		//   - hdf
		//
		// initExecutable(executableBackend, dataOutputBackend)
		//   combinations:
		//   - docker/csv
		//   - docker/hdf
		//   - spack/csv
		//   - spack/hdf
		//   - ...
		//
		// initOrchestrator(executableBackend, orchestratorBackend)
		//   combinations:
		//   - spack/slurm
		//   - docker/slurm
		//   - spack/ansible
		//   - docker/ansible
		//   - ...
		//
		// initViz(dataOutputBackend, vizBackend)
		//   combinations:
		//   - csv/jupyter
		//   - csv/other
		//   - hdf/jupyter
		//   - hdf/other
		//   - ...
		//
		// initChecker(dataOutputBackend)
		//   options:
		//   - aver
		//   - other
	},
}

func init() {
	RootCmd.AddCommand(initCmd)
	initCmd.Flags().StringVarP(&executor, "executor", "e", "ansible", "Executor backend")
}
