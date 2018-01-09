package main

import (
	"fmt"
	"log"

	"github.com/spf13/cobra"
	"github.com/theherk/viper"
)

var metaForceFlag bool

func getMeta(args []string) {
	ensureInRootFolder()
	err := readPopperConfig()
	if err != nil {
		log.Fatalln(err)
	}
	if !viper.IsSet("metadata") || len(viper.GetStringMapString("metadata")) == 0 {
		fmt.Println("No metadata entries yet.")
		return
	}
	if len(args) == 0 {
		values := viper.GetStringMapString("metadata")
		for k, v := range values {
			fmt.Printf("%s: '%s'\n", k, v)
		}
		return
	}

	keyName := args[0]

	if viper.IsSet("metadata." + keyName) {
		fmt.Printf("'%s'\n", viper.GetString("metadata."+keyName))
	} else {
		fmt.Println("Cannot find key " + keyName)
	}
}

var metaCmd = &cobra.Command{
	Use:   "metadata",
	Short: "Add/remove metadata for a repository.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		getMeta([]string{})
	},
}
var metaSetCmd = &cobra.Command{
	Use:   "set <key> '<value>'",
	Short: "Add a new metadata element.",
	Long:  "Adds a key-value pair to the metadata of the article. The key should not contain spaces.",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 2 {
			log.Fatalln("This command only takes two arguments.")
		}
		ensureInRootFolder()
		err := readPopperConfig()
		if err != nil {
			log.Fatalln(err)
		}
		values := map[string]string{}
		if viper.IsSet("metadata") {
			values = viper.GetStringMapString("metadata")

			if viper.IsSet("metadata."+args[0]) && !metaForceFlag {
				fmt.Println("Key '" + args[0] + "' already assigned, add '-f' to overwrite it.")
				return
			}
		}
		values[args[0]] = args[1]
		viper.Set("metadata", values)
		viper.WriteConfig()
		fmt.Println("Added " + args[0] + ": '" + args[1] + "'")
	},
}
var metaGetCmd = &cobra.Command{
	Use:   "get [<key>]",
	Short: "Obtain metadata for the repo. All keys get displayed if none is given.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) > 1 {
			log.Fatalln("This command takes at most one argument.")
		}
		getMeta(args)
	},
}

func init() {
	RootCmd.AddCommand(metaCmd)
	metaCmd.AddCommand(metaSetCmd)
	metaCmd.AddCommand(metaGetCmd)
	metaSetCmd.Flags().BoolVarP(&metaForceFlag, "force", "f", false, "Overwrite metadata value.")
}
