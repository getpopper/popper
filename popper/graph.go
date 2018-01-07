package main

import (
	"bytes"
	"fmt"
	"hash/fnv"
	"io/ioutil"
	"log"
	"strings"

	sh "github.com/codeskyblue/go-sh"
	"github.com/spf13/cobra"
	"mvdan.cc/sh/syntax"
)

func hashIt(s string) uint32 {
	h := fnv.New32a()
	h.Write([]byte(s))
	return h.Sum32()
}

func getDotGraphForStage(pipelinePath, stageFile, previousStageFile string) (dot string, err error) {
	content, err := ioutil.ReadFile(pipelinePath + "/" + stageFile)
	if err != nil {
		return
	}
	f, err := syntax.NewParser(syntax.KeepComments).Parse(bytes.NewReader(content), "")
	if err != nil {
		return
	}

	dot = ""

	stage := strings.Replace(stageFile, ".sh", "", -1)
	stage = strings.Replace(stage, "-", "", -1)

	posIfClause := uint(0)
	endIfClause := uint(0)
	ifClauseNodeId := uint(0)
	nodesInGraph := make(map[uint32]bool)

	// walk the walk
	syntax.Walk(f, func(node syntax.Node) bool {
		label := ""
		foundWfComment := false
		switch x := node.(type) {
		case *syntax.Stmt:
			if len(x.Comments) == 0 {
				return true
			}
			for _, c := range x.Comments {

				// ignore statements without [wf]
				if !strings.Contains(c.Text, "[wf]") {
					continue
				}
				foundWfComment = true

				// get the label of the node
				label = strings.Replace(c.Text, " [wf] ", "", 1)
				label = strings.Replace(label, "[wf]", "", 1)
				label = strings.Replace(label, " [wf]", "", 1)
				label = strings.Replace(label, "[wf] ", "", 1)
			}

			if !foundWfComment {
				return true
			}

			// first comment in a script goes in the root of that stage
			if _, present := nodesInGraph[hashIt(stage)]; !present {
				dot += fmt.Sprintf("  %s [shape=record,style=filled,label=\"{%s|%s}\"];\n", stage, stageFile, label)

				if len(previousStageFile) > 0 {
					previous := strings.Replace(previousStageFile, ".sh", "", -1)
					previous = strings.Replace(previous, "-", "", -1)
					dot += fmt.Sprintf("  %s -> %s;\n", previous, stage)
				}
				nodesInGraph[hashIt(stage)] = true
				return true
			}

			// add any clause-specific elements to label

			switch y := x.Cmd.(type) {
			case *syntax.CallExpr:

				cmdValue := ""
				for _, w := range y.Args {
					for _, wp := range w.Parts {
						switch x := wp.(type) {
						case *syntax.Lit:
							cmdValue = x.Value
						default:
							cmdValue = "unknownCmd"
						}
						break
					}
					break
				}
				label = cmdValue + ": " + label
			case *syntax.ForClause:
				label = "loop: " + label
			case *syntax.WhileClause:
				label = "loop: " + label
			case *syntax.CaseClause:
				label = "case: " + label
			}

			dot += fmt.Sprintf("  s%d [shape=record,label=\"%s\"];\n", x.Pos().Offset(), label)

			// add edges
			if x.Pos().Offset() > posIfClause && x.End().Offset() < endIfClause {

				if _, present := nodesInGraph[uint32(posIfClause)]; !present {
					// add the ifClause node
					dot += fmt.Sprintf("  s%d [label=\"condition\"];\n", ifClauseNodeId)
					// add a link from stage to it
					dot += fmt.Sprintf("  %s -> s%d;\n", stage, ifClauseNodeId)
					nodesInGraph[uint32(posIfClause)] = false
				}

				// within an if statement, create edge from if clause node
				dot += fmt.Sprintf("  s%d -> s%d;\n", ifClauseNodeId, x.Pos().Offset())
			} else {
				// create edge from stage node
				dot += fmt.Sprintf("  %s -> s%d;\n", stage, x.Pos().Offset())
			}
		case *syntax.IfClause:

			// get position of current if clause
			posIfClause = x.Pos().Offset()
			endIfClause = x.End().Offset()
			ifClauseNodeId = x.Pos().Offset()

			// TODO: support nested if clauses, e.g. by using a stack
		}
		return true
	})
	return
}

func getDotGraph(pipelinePath string, stages []string) (dot string, err error) {
	dot = "digraph pipeline {\n"
	previousStage := ""

	for _, stage := range stages {

		if !sh.Test("f", pipelinePath+"/"+stage) {
			continue
		}
		if subdot, err := getDotGraphForStage(pipelinePath, stage, previousStage); err != nil {
			return "", err
		} else {
			dot += subdot
		}

		previousStage = stage
	}

	dot += "}"

	return
}

var graphCmd = &cobra.Command{
	Use:   "workflow [pipeline]",
	Short: "Obtain a call graph of a pipeline in .dot format.",
	Long:  "",
	Run: func(cmd *cobra.Command, args []string) {

		if len(args) > 1 {
			log.Fatalln("This command takes one argument at most.")
		}

		pipelinePath, stages := getPipelineStages(args)

		dot, err := getDotGraph(pipelinePath, stages)
		if err != nil {
			log.Fatalln(err)
		}

		fmt.Println(dot)
	},
}

func init() {
	RootCmd.AddCommand(graphCmd)
}
