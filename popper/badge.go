package main

import (
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
			HandleFunc("/{orgId}/{repoId}/{expId}/{sha}/{status}", handleExperiment).
			Methods("POST")

		// Get most recent badge
		router.
			HandleFunc("/{orgId}/{repoId}/{expId}/status.svg", getLatestBadge).
			Methods("GET")

		// Get badge for specific SHA
		router.
			HandleFunc("/{orgId}/{repoId}/{expId}/{sha}/status.svg", getSpecificBadge).
			Methods("GET")

		log.Fatal(http.ListenAndServe(":9090", router))
	},
}

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Check experiment(s) status stored with badge service.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		var sha string
		if len(args) == 1 {
			sha = args[1]
			expName, err := getExperimentName()
			if err != nil {
				return
			}
			orgName, repoName, err := getRepoInfo()
			if err != nil {
				return
			}
			getString := "http://status.falsifiable.us/" + orgName + "/" + repoName + "/" + expName + "/" + sha + "/status.svg"

			req := http.Get(getString)
		} else if len(args) == 0 {
			if !sh.Test("dir", "validate.sh") {
				log.Fatalln("Can't find validate.sh. Are you in the root folder of an experiment?")
			} else {
				sha, err := sh.Command("git", "rev-parse", "HEAD").Output()
				if err != nil {
					return
				}
				expName, err := getExperimentName()
				if err != nil {
					return
				}
				orgName, repoName, err := getRepoInfo()
				if err != nil {
					return
				}
				getString := "http://status.falsifiable.us/" + orgName + "/" + repoName + "/" + expName + "/" + sha + "/status.svg"

				req := http.Get(getString)
			}
		} else {
			log.Fatalln("This command takes one argument at most.")
		}
	},
}

func getExperimentStatus(w http.ResponseWriter, orgId, repoId, expId, sha string) (expStatus string) {
	// Open database, creates if necessary
	db, err := bolt.Open("status.db", 0600, nil)
	if err != nil {
		log.Fatal(err)
	}

	// Close database when function ends
	defer db.Close()

	// Identify buckets based on experiment ID
	err = db.View(func(tx *bolt.Tx) error {
		orgBucket := tx.Bucket([]byte(orgId))
		if orgBucket == nil {
			expStatus = "invalid"
			return nil
		}

		repoBucket := orgBucket.Bucket([]byte(repoId))
		if repoBucket == nil {
			expStatus = "invalid"
			return nil
		}

		expBucket := repoBucket.Bucket([]byte(expId))
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
	orgId := vars["orgId"]
	repoId := vars["repoId"]
	expId := vars["expId"]
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
		orgBucket, err := tx.CreateBucketIfNotExists([]byte(orgId))
		if err != nil {
			log.Println(err.Error())
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return nil
		}
		repoBucket, err := orgBucket.CreateBucketIfNotExists([]byte(repoId))
		if err != nil {
			log.Println(err.Error())
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return nil
		}
		expBucket, err := repoBucket.CreateBucketIfNotExists([]byte(expId))
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
	orgId := vars["orgId"]
	repoId := vars["repoId"]
	expId := vars["expId"]
	sha := "current"

	getBadge(w, orgId, repoId, expId, sha)
}

func getSpecificBadge(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	orgId := vars["orgId"]
	repoId := vars["repoId"]
	expId := vars["expId"]
	sha := vars["sha"]

	getBadge(w, orgId, repoId, expId, sha)
}

func getBadge(w http.ResponseWriter, orgId, repoId, expId, sha string) {
	exp := getExperimentStatus(w, orgId, repoId, expId, sha)
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
	badgeCmd.addCommand(statusCmd)
}
