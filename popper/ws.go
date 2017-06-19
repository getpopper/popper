package main

import (
	"bytes"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/user"
	"path"
	"strings"
	"time"

	sh "github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
)

var wsFolder string
var commitMsg string

var wsCmd = &cobra.Command{
	Use:   "ws",
	Short: "Manage test results.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		log.Fatalln("Can't use this subcommand directly. See 'popper help ws' for usage")
	},
}

var wsLogCmd = &cobra.Command{
	Use:   "log",
	Short: "Show workspace commit log for this experiment.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) > 0 {
			log.Fatalln("This command doesn't take arguments.")
		}
		checkWeInExperimentFolder()
		expFolder := getWsExperimentFolderPath()
		commitFolders, _ := ioutil.ReadDir(expFolder)
		for _, f := range commitFolders {
			if strings.HasPrefix(f.Name(), ".") {
				continue
			}
			sha, err := sh.Command("cat", expFolder+"/"+f.Name()+"/commit").CombinedOutput()
			if err != nil {
				fmt.Printf("%s\n", string(sha[:]))
				log.Fatalln(err)
			}
			msg, err := sh.
				Command("cat", expFolder+"/"+f.Name()+"/message").
				Command("head", "-n1").
				CombinedOutput()
			if err != nil {
				fmt.Printf("%s\n", string(msg[:]))
				log.Fatalln(err)
			}
			fmt.Printf("%s@%s %s\n", f.Name(), bytes.TrimSpace(sha), bytes.TrimSpace(msg))
		}
	},
}
var wsShowCmd = &cobra.Command{
	Use:   "show <commit-id>",
	Short: "Show information about a commit.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 1 {
			log.Fatalln("This command takes one argument (commit ID).")
		}
		commitid := strings.Split(args[0], "@")
		ts := commitid[0]
		commitFolder := getWsExperimentFolderPath() + "/" + ts
		if err := sh.Command("cat", commitFolder+"/message").Run(); err != nil {
			log.Fatalln(err)
		}
		if err := sh.Command("echo", "\n\nfolder: ", commitFolder).Run(); err != nil {
			log.Fatalln(err)
		}
	},
}
var wsCheckoutCmd = &cobra.Command{
	Use:   "checkout <commit-id>",
	Short: "Checkout a workspace commit.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 1 {
			log.Fatalln("This command takes one argument (commit ID).")
		}
		commitid := strings.Split(args[0], "@")
		ts := commitid[0]
		commitFolder := getWsExperimentFolderPath() + "/" + ts
		if out, err := sh.Command("cp", "-r", commitFolder+"/files/.", ".").CombinedOutput(); err != nil {
			fmt.Println("%s\n", string(out[:]))
			log.Fatalln(err)
		}
	},
}
var wsCommitCmd = &cobra.Command{
	Use:   "commit",
	Short: "Commit any file that is not tracked by the VCS.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) > 0 {
			log.Fatalln("This command doesn't take arguments.")
		}
		checkWeInExperimentFolder()
		if _, err := sh.Command("rsync", "--version").CombinedOutput(); err != nil {
			log.Fatalln("Can't invoke rsync.")
		}
		ts := int32(time.Now().Unix())
		commitFolder := getWsExperimentFolderPath() + "/" + fmt.Sprintf("%v", ts)
		if err := sh.Command("mkdir", "-p", commitFolder+"/files").Run(); err != nil {
			log.Fatalln(err)
		}

		// git ls-files --others --exclude-standard -z | rsync --files-from=- -0 --no-dirs --whole-file . <folder>
		err := sh.
			Command("git", "ls-files", "--others", "--exclude-standard", "-z").
			Command("rsync", "--files-from=-", "-0", "--no-dirs", "--whole-file", ".", commitFolder+"/files").
			Run()
		if err != nil {
			log.Fatalln(err)
		}
		if err := ioutil.WriteFile(commitFolder+"/message", []byte(commitMsg), 0644); err != nil {
			log.Fatalln(err)
		}
		sha, err := sh.Command("git", "rev-parse", "--short", "HEAD").CombinedOutput()
		if err != nil {
			log.Fatalln(err)
		}
		if err := ioutil.WriteFile(commitFolder+"/commit", []byte(sha), 0644); err != nil {
			log.Fatalln(err)
		}
		fmt.Printf("%v@%s %s\n\n", ts, bytes.TrimSpace(sha), commitMsg)
		fmt.Println("Add more details to: " + commitFolder + "/message")
	},
}

func getWsExperimentFolderPath() string {
	expName, _ := os.Getwd()
	expName = path.Base(expName)
	user, repo, err := getRepoInfo()
	if err != nil {
		log.Fatalln(err)
	}
	return wsFolder + "/" + user + "/" + repo + "/" + expName
}

func init() {
	RootCmd.AddCommand(wsCmd)
	wsCmd.AddCommand(wsCommitCmd)
	wsCmd.AddCommand(wsLogCmd)
	wsCmd.AddCommand(wsCheckoutCmd)
	wsCmd.AddCommand(wsShowCmd)

	usr, err := user.Current()
	if err != nil {
		log.Fatal(err)
	}
	wsCommitCmd.Flags().StringVarP(&commitMsg, "message", "m", "", "Commit message.")
	wsCommitCmd.Flags().StringVarP(&wsFolder, "folder", "f", usr.HomeDir+"/popperws", "Path to workspace folder.")
}
