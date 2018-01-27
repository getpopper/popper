package main

import (
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"time"

	"github.com/boltdb/bolt"
	sh "github.com/codeskyblue/go-sh"
	"github.com/gorilla/mux"
	"github.com/spf13/cobra"
)

var badgeCmd = &cobra.Command{
	Use:   "badge",
	Short: "Run a badge server and generate link to badges.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		log.Fatalln("Can't use this subcommand directly. See 'popper help ci' for usage")
	},
}

var serviceCmd = &cobra.Command{
	Use:   "service",
	Short: "Start a badge server instance.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 0 {
			log.Fatalln("This command doesn't take arguments.")
		}

		router := mux.NewRouter().StrictSlash(true)

		// Update experiment status
		router.
			HandleFunc("/{orgID}/{repoID}/{expID}/{sha}/{status}", handleExperiment).
			Methods("POST")

		// Get most recent badge
		router.
			HandleFunc("/{orgID}/{repoID}/{expID}/status.svg", getLatestBadge).
			Methods("GET")

		// Get most recent status for CLI
		router.
			HandleFunc("/{orgID}/{repoID}/{expID}/status", getLatestStatus).
			Methods("GET")

		// Get status history for CLI
		router.
			HandleFunc("/{orgID}/{repoID}/{expID}/history", getHistory).
			Methods("GET")

		// Get badge for specific SHA
		router.
			HandleFunc("/{orgID}/{repoID}/{expID}/{sha}/status.svg", getSpecificBadge).
			Methods("GET")

		log.Fatal(http.ListenAndServe(":9090", router))
	},
}

func status(cmd *cobra.Command, args []string) {
	if len(args) > 1 {
		log.Fatalln("This command takes one argument at most.")
		return
	}

	var expName string
	var err error
	if len(args) == 1 {
		expName = args[1]
	} else {
		if !sh.Test("dir", "validate.sh") {
			log.Fatalln("Can't find validate.sh. Are you in the root folder of an experiment?")
			return
		}

		expName, err = getExperimentName()
		if err != nil {
			log.Fatalln("Unable to get experiment name.")
		}

	}

	orgName, repoName, err := getRepoInfo()
	if err != nil {
		return
	}
	requestString := "http://status.falsifiable.us/" + orgName + "/" + repoName + "/" + expName + "/status"
	response, err := http.Get(requestString)
	if err != nil {
		return
	}
	defer response.Body.Close()
	body, err := ioutil.ReadAll(response.Body)
	fmt.Println(body)
}

var (
	// alias for status
	statusCmd = &cobra.Command{
		Use:   "status",
		Short: "Check experiment(s) status stored with badge service.",
		Long:  ``,
		Run:   status,
	}
	linkCmd = &cobra.Command{
		Hidden: true,
		Use:    "link",
		Short:  "Check experiment(s) status stored with badge service.",
		Long:   ``,
		Run:    status,
	}

	statusLinkCmd = &cobra.Command{
		Hidden: true,
		Use:    "status-link",
		Short:  "Check experiment(s) status stored with badge service.",
		Long:   ``,
		Run:    status,
	}
)

var historyCmd = &cobra.Command{
	Use:   "history",
	Short: "List experiment status history stored with badge service.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) > 1 {
			log.Fatalln("This command takes one argument at most.")
			return
		}

		var expName string
		var err error
		if len(args) == 1 {
			expName = args[1]
		} else {
			if !sh.Test("dir", "validate.sh") {
				log.Fatalln("Can't find validate.sh. Are you in the root folder of an experiment?")
				return
			}

			expName, err = getExperimentName()
			if err != nil {
				log.Fatalln("Unable to get experiment name.")
			}

		}

		orgName, repoName, err := getRepoInfo()
		if err != nil {
			return
		}
		requestString := "http://status.falsifiable.us/" + orgName + "/" + repoName + "/" + expName + "/history"
		response, err := http.Get(requestString)
		if err != nil {
			return
		}
		defer response.Body.Close()
		body, err := ioutil.ReadAll(response.Body)
		fmt.Println(body)
	},
}

func getExperimentStatus(w http.ResponseWriter, orgID, repoID, expID, sha string) (expStatus string) {
	// Open database, creates if necessary
	db, err := bolt.Open("status.db", 0600, nil)
	if err != nil {
		log.Fatal(err)
	}

	// Close database when function ends
	defer db.Close()

	// Identify buckets based on experiment ID
	err = db.View(func(tx *bolt.Tx) error {
		orgBucket := tx.Bucket([]byte(orgID))
		if orgBucket == nil {
			expStatus = "invalid"
			return nil
		}

		repoBucket := orgBucket.Bucket([]byte(repoID))
		if repoBucket == nil {
			expStatus = "invalid"
			return nil
		}

		expBucket := repoBucket.Bucket([]byte(expID))
		if expBucket == nil {
			expStatus = "invalid"
			return nil
		}
		// Each experiment is a bucket with SHA's stored as keys, status as value
		status := expBucket.Get([]byte(sha))
		expStatus = string(status)
		return nil
	})

	return expStatus
}

var badges = map[string][]byte{
	"invalid": []byte(`<svg xmlns="http://www.w3.org/2000/svg" width="108" height="20"><linearGradient id="b" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient><mask id="a"><rect width="108" height="20" rx="3" fill="#fff"/></mask><g mask="url(#a)"><path fill="#555" d="M0 0h47v20H0z"/><path fill="#9f9f9f" d="M47 0h61v20H47z"/><path fill="url(#b)" d="M0 0h108v20H0z"/></g><g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11"><text x="23.5" y="15" fill="#010101" fill-opacity=".3">Popper</text><text x="23.5" y="14">Popper</text><text x="76.5" y="15" fill="#010101" fill-opacity=".3">unknown</text><text x="76.5" y="14">unknown</text></g></svg>`),
	"fail":    []byte(`<svg xmlns="http://www.w3.org/2000/svg" width="82" height="20"><linearGradient id="b" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient><mask id="a"><rect width="82" height="20" rx="3" fill="#fff"/></mask><g mask="url(#a)"><path fill="#555" d="M0 0h47v20H0z"/><path fill="#e05d44" d="M47 0h35v20H47z"/><path fill="url(#b)" d="M0 0h82v20H0z"/></g><g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11"><text x="23.5" y="15" fill="#010101" fill-opacity=".3">Popper</text><text x="23.5" y="14">Popper</text><text x="63.5" y="15" fill="#010101" fill-opacity=".3">FAIL</text><text x="63.5" y="14">FAIL</text></g></svg>`),
	"ok":      []byte(`<svg xmlns="http://www.w3.org/2000/svg" width="74" height="20"><linearGradient id="b" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient><mask id="a"><rect width="74" height="20" rx="3" fill="#fff"/></mask><g mask="url(#a)"><path fill="#555" d="M0 0h47v20H0z"/><path fill="#4c1" d="M47 0h27v20H47z"/><path fill="url(#b)" d="M0 0h74v20H0z"/></g><g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11"><text x="23.5" y="15" fill="#010101" fill-opacity=".3">Popper</text><text x="23.5" y="14">Popper</text><text x="59.5" y="15" fill="#010101" fill-opacity=".3">OK</text><text x="59.5" y="14">OK</text></g></svg>`),
	"gold":    []byte(`<svg xmlns="http://www.w3.org/2000/svg" width="88" height="20"><linearGradient id="b" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient><mask id="a"><rect width="88" height="20" rx="3" fill="#fff"/></mask><g mask="url(#a)"><path fill="#555" d="M0 0h47v20H0z"/><path fill="#dfb317" d="M47 0h41v20H47z"/><path fill="url(#b)" d="M0 0h88v20H0z"/></g><g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11"><text x="23.5" y="15" fill="#010101" fill-opacity=".3">Popper</text><text x="23.5" y="14">Popper</text><text x="66.5" y="15" fill="#010101" fill-opacity=".3">GOLD</text><text x="66.5" y="14">GOLD</text></g></svg>`),
}

func handleExperiment(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	orgID := vars["orgID"]
	repoID := vars["repoID"]
	expID := vars["expID"]
	sha := vars["sha"]
	status := vars["status"]

	// Open db
	db, err := bolt.Open("status.db", 0600, nil)
	if err != nil {
		log.Fatal(err)
	}

	// Close when handler is finished
	defer db.Close()

	// Create status entry
	// Creates buckets as necessary (for new entries)
	db.Update(func(tx *bolt.Tx) error {
		orgBucket, err := tx.CreateBucketIfNotExists([]byte(orgID))
		if err != nil {
			log.Println(err.Error())
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return nil
		}
		repoBucket, err := orgBucket.CreateBucketIfNotExists([]byte(repoID))
		if err != nil {
			log.Println(err.Error())
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return nil
		}
		expBucket, err := repoBucket.CreateBucketIfNotExists([]byte(expID))
		if err != nil {
			log.Println(err.Error())
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return nil
		}
		expBucket.Put([]byte(sha), []byte(status))

		// Update the current key with the latest status to make it easy to grab
		expBucket.Put([]byte("current"), []byte(status))
		return nil
	})

}

// Two wrappers for getBadge to return either a specific badge or just the latest one
func getLatestBadge(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	orgID := vars["orgID"]
	repoID := vars["repoID"]
	expID := vars["expID"]
	sha := "current"

	getBadge(w, orgID, repoID, expID, sha)
}

func getSpecificBadge(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	orgID := vars["orgID"]
	repoID := vars["repoID"]
	expID := vars["expID"]
	sha := vars["sha"]

	getBadge(w, orgID, repoID, expID, sha)
}

// Return current status for CLI status command
func getLatestStatus(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	orgID := vars["orgID"]
	repoID := vars["repoID"]
	expID := vars["expID"]
	sha := "current"

	status := getExperimentStatus(w, orgID, repoID, expID, sha)
	w.Write([]byte(status))
}

// Return status history as a list
func getHistory(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	orgID := vars["orgID"]
	repoID := vars["repoID"]
	expID := vars["expID"]

	// Open database, creates if necessary
	db, err := bolt.Open("status.db", 0600, nil)
	if err != nil {
		log.Fatal(err)
	}

	// Close database when function ends
	defer db.Close()

	// Identify buckets based on experiment ID
	err = db.View(func(tx *bolt.Tx) error {
		orgBucket := tx.Bucket([]byte(orgID))
		if orgBucket == nil {
			return nil
		}

		repoBucket := orgBucket.Bucket([]byte(repoID))
		if repoBucket == nil {
			return nil
		}

		expBucket := repoBucket.Bucket([]byte(expID))
		if expBucket == nil {
			return nil
		}

		cursor := expBucket.Cursor()

		var history []byte

		for sha, status := cursor.First(); sha != nil; sha, status = cursor.Next() {
			line := string(sha) + " " + string(status) + "\n"
			history = append(history, line...)
		}
		w.Write(history)
		return nil
	})
	return
}

func getBadge(w http.ResponseWriter, orgID, repoID, expID, sha string) {
	exp := getExperimentStatus(w, orgID, repoID, expID, sha)
	date := time.Now().Format(http.TimeFormat)
	log.Printf("%v\n", date)
	log.Printf("State %v\n", exp)
	w.Header().Set("Content-Type", "image/svg+xml")
	w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
	w.Header().Set("Date", date)
	w.Header().Set("Expires", date)
	switch exp {
	case "invalid":
		w.Write(badges["invalid"])
		break
	case "ok":
		w.Write(badges["ok"])
		break
	case "fail":
		w.Write(badges["fail"])
		break
	case "gold":
		w.Write(badges["gold"])
		break
	}
}

func init() {
	RootCmd.AddCommand(badgeCmd)
	badgeCmd.AddCommand(serviceCmd)
	badgeCmd.AddCommand(statusCmd)
}
