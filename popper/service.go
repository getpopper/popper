package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"

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

		log.Fatal(http.ListenAndServe(":9090", router))
	},
}

type Experiment struct {
	Name   string `json:"name"`
	Status string `json:"status"`
}

var repos = map[string]map[string]*Experiment{}

func handleExperiment(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	vars := mux.Vars(r)
	repoId := vars["repoId"]
	expId := vars["expId"]

	switch r.Method {
	case "GET":
		experiment := new(Experiment)

		repo, ok := repos[repoId]
		if !ok {
			w.WriteHeader(http.StatusNotFound)
			fmt.Fprintln(w, string("Repo not found"))
			return
		} else {
			experiment, ok = repo[expId]
			if !ok {
				w.WriteHeader(http.StatusNotFound)
				fmt.Fprintln(w, string("Experiment not found"))
				return
			}
		}

		outgoingJSON, error := json.Marshal(experiment)

		if error != nil {
			log.Println(error.Error())
			http.Error(w, error.Error(), http.StatusInternalServerError)
			return
		}
		fmt.Fprint(w, string(outgoingJSON))

	case "POST":
		experiment := new(Experiment)
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
			repos[repoId] = map[string]*Experiment{}
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

func init() {
	RootCmd.AddCommand(serviceCmd)
}
