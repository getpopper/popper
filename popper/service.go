package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/gorilla/mux"
	"github.com/spf13/cobra"
)

var serviceCmd = &cobra.Command{
	Use:   "service",
	Short: "Start experiment status service.",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) != 0 {
			log.Fatalln("This command doesn't take arguments.")
		}

		router := mux.NewRouter().StrictSlash(true)

		router.
			HandleFunc("/repos/{repoId}/{expId}", handleExperiment).
			Methods("GET", "POST")
		router.
			HandleFunc("/repos/{repoId}/{expId}/status.svg", handleBadge).
			Methods("GET")

		log.Fatal(http.ListenAndServe(":9090", router))
	},
}

type ExperimentStatus struct {
	Name   string `json:"name"`
	Status string `json:"status"`
}

func getExperimentStatus(w http.ResponseWriter, repoId, expId string) (exp *ExperimentStatus) {
	exp = new(ExperimentStatus)

	repo, ok := repos[repoId]
	if !ok {
		exp.Status = "invalid"
		return
	} else {
		exp, ok = repo[expId]
		if !ok {
			exp.Status = "invalid"
			return
		}
	}

	return
}

var repos = map[string]map[string]*ExperimentStatus{}
var badges = map[string][]byte{
	"invalid": []byte(`<svg xmlns="http://www.w3.org/2000/svg" width="108" height="20"><linearGradient id="b" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient><mask id="a"><rect width="108" height="20" rx="3" fill="#fff"/></mask><g mask="url(#a)"><path fill="#555" d="M0 0h47v20H0z"/><path fill="#9f9f9f" d="M47 0h61v20H47z"/><path fill="url(#b)" d="M0 0h108v20H0z"/></g><g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11"><text x="23.5" y="15" fill="#010101" fill-opacity=".3">Popper</text><text x="23.5" y="14">Popper</text><text x="76.5" y="15" fill="#010101" fill-opacity=".3">unknown</text><text x="76.5" y="14">unknown</text></g></svg>`),
	"fail":    []byte(`<svg xmlns="http://www.w3.org/2000/svg" width="82" height="20"><linearGradient id="b" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient><mask id="a"><rect width="82" height="20" rx="3" fill="#fff"/></mask><g mask="url(#a)"><path fill="#555" d="M0 0h47v20H0z"/><path fill="#e05d44" d="M47 0h35v20H47z"/><path fill="url(#b)" d="M0 0h82v20H0z"/></g><g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11"><text x="23.5" y="15" fill="#010101" fill-opacity=".3">Popper</text><text x="23.5" y="14">Popper</text><text x="63.5" y="15" fill="#010101" fill-opacity=".3">FAIL</text><text x="63.5" y="14">FAIL</text></g></svg>`),
	"ok":      []byte(`<svg xmlns="http://www.w3.org/2000/svg" width="74" height="20"><linearGradient id="b" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient><mask id="a"><rect width="74" height="20" rx="3" fill="#fff"/></mask><g mask="url(#a)"><path fill="#555" d="M0 0h47v20H0z"/><path fill="#4c1" d="M47 0h27v20H47z"/><path fill="url(#b)" d="M0 0h74v20H0z"/></g><g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11"><text x="23.5" y="15" fill="#010101" fill-opacity=".3">Popper</text><text x="23.5" y="14">Popper</text><text x="59.5" y="15" fill="#010101" fill-opacity=".3">OK</text><text x="59.5" y="14">OK</text></g></svg>`),
	"gold":    []byte(`<svg xmlns="http://www.w3.org/2000/svg" width="88" height="20"><linearGradient id="b" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient><mask id="a"><rect width="88" height="20" rx="3" fill="#fff"/></mask><g mask="url(#a)"><path fill="#555" d="M0 0h47v20H0z"/><path fill="#dfb317" d="M47 0h41v20H47z"/><path fill="url(#b)" d="M0 0h88v20H0z"/></g><g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11"><text x="23.5" y="15" fill="#010101" fill-opacity=".3">Popper</text><text x="23.5" y="14">Popper</text><text x="66.5" y="15" fill="#010101" fill-opacity=".3">GOLD</text><text x="66.5" y="14">GOLD</text></g></svg>`),
}

func handleExperiment(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	vars := mux.Vars(r)
	repoId := vars["repoId"]
	expId := vars["expId"]

	switch r.Method {
	case "GET":
		exp := getExperimentStatus(w, repoId, expId)
		if exp.Status == "invalid" {
			w.WriteHeader(http.StatusNotFound)
			fmt.Fprintln(w, string("Repo or user not found"))
		}
		outgoingJSON, error := json.Marshal(exp)

		if error != nil {
			log.Println(error.Error())
			http.Error(w, error.Error(), http.StatusInternalServerError)
			return
		}
		fmt.Fprint(w, string(outgoingJSON))

	case "POST":
		experiment := new(ExperimentStatus)
		decoder := json.NewDecoder(r.Body)
		error := decoder.Decode(&experiment)
		if error != nil {
			log.Println(error.Error())
			http.Error(w, error.Error(), http.StatusInternalServerError)
			return
		}
		repo, ok := repos[repoId]
		if !ok {
			log.Println("Didn't find repo " + repoId + "; adding it")
			repos[repoId] = map[string]*ExperimentStatus{}
			repo = repos[repoId]
		}
		experiment.Name = expId

		repo[expId] = experiment

		outgoingJSON, err := json.Marshal(experiment)
		if err != nil {
			log.Println(error.Error())
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.WriteHeader(http.StatusCreated)
		fmt.Fprint(w, string(outgoingJSON))
	}
}

func handleBadge(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	repoId := vars["repoId"]
	expId := vars["expId"]

	switch r.Method {
	case "GET":
		exp := getExperimentStatus(w, repoId, expId)
		date := time.Now().Format(http.TimeFormat)
		log.Printf("%v\n", date)
		log.Printf("State %v\n", exp)
		w.Header().Set("Content-Type", "image/svg+xml")
		w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
		w.Header().Set("Date", date)
		w.Header().Set("Expires", date)
		switch exp.Status {
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
}

func init() {
	RootCmd.AddCommand(serviceCmd)
}
