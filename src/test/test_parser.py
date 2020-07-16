import unittest

from popper.parser import WorkflowParser
from popper.cli import log


class TestWorkflow(unittest.TestCase):
    def setUp(self):
        log.setLevel("CRITICAL")

    def tearDown(self):
        log.setLevel("NOTSET")

    def test_empty_file(self):
        try:
            f = open("test.yml", "a")
            f.close()
            WorkflowParser.parse(file="test.yml")
            self.assertTrue(False, "Empty Workflow file does not raise an exception.")
        except SystemExit:
            self.assertTrue(True)
        else:
            self.assertTrue(False, "Empty Workflow file does not raise a SystemExit.")

    def test_new_workflow(self):
        wf_data = {}
        self.assertRaises(SystemExit, WorkflowParser.parse, **{"wf_data": wf_data})

        wf_data = {"unexpected": []}
        self.assertRaises(SystemExit, WorkflowParser.parse, **{"wf_data": wf_data})

        wf_data = {
            "steps": [
                {
                    "uses": "foo",
                    "id": "step",
                    "env": {"EN": "EE"},
                    "secrets": ["S"],
                    "dir": "/path/to/",
                    "options": {"name": "spam"},
                },
                {"uses": "bar", "runs": ["a", "b"], "args": ["c"], "skip_pull": True},
            ],
            "options": {"env": {"FOO": "bar"}, "secrets": ["Z"],},
        }
        wf = WorkflowParser.parse(wf_data=wf_data)

        step = wf.steps[0]
        self.assertEqual("step", step.id)
        self.assertEqual("foo", step.uses)
        self.assertEqual(("Z", "S"), step.secrets)
        self.assertEqual({"EN": "EE", "FOO": "bar"}, step.env)
        self.assertEqual("/path/to/", step.dir)
        self.assertEqual("spam", step.options.name)
        self.assertTrue(not step.runs)
        self.assertTrue(not step.args)
        self.assertFalse(step.skip_pull)

        step = wf.steps[1]
        self.assertEqual("bar", step.uses)
        self.assertEqual(("a", "b"), step.runs)
        self.assertEqual(("c",), step.args)
        self.assertTrue(step.skip_pull)
        self.assertTrue(not step.dir)
        self.assertEqual({"FOO": "bar"}, step.env)
        self.assertEqual(("Z",), step.secrets)
        self.assertEqual({"FOO": "bar"}, wf.options.env)
        self.assertEqual(("Z",), wf.options.secrets)

    def test_filter_all_but_given_step(self):
        wf_data = {
            "steps": [
                {"uses": "foo", "id": "one"},
                {"uses": "bar", "id": "two"},
                {"uses": "baz", "id": "three"},
            ]
        }
        wf = WorkflowParser.parse(wf_data=wf_data, step="two")
        self.assertEqual(1, len(wf.steps))
        self.assertEqual("two", wf.steps[0].id)
        self.assertEqual("bar", wf.steps[0].uses)

        # non-existing name
        self.assertRaises(
            SystemExit, WorkflowParser.parse, **{"wf_data": wf_data, "step": "four"}
        )

        # without id
        wf_data = {"steps": [{"uses": "foo"}, {"uses": "bar"}, {"uses": "baz"},]}
        wf = WorkflowParser.parse(wf_data=wf_data, step="2")
        self.assertEqual(1, len(wf.steps))
        self.assertEqual("2", wf.steps[0].id)

    def test_skip_steps(self):
        wf_data = {
            "steps": [
                {"uses": "foo", "id": "one"},
                {"uses": "bar", "id": "two"},
                {"uses": "baz", "id": "three"},
            ]
        }
        # skip one step
        wf = WorkflowParser.parse(wf_data=wf_data, skipped_steps=["two"])
        self.assertEqual(2, len(wf.steps))
        self.assertEqual("one", wf.steps[0].id)
        self.assertEqual("three", wf.steps[1].id)

        # more than one
        wf = WorkflowParser.parse(wf_data=wf_data, skipped_steps=["one", "three"])
        self.assertEqual(1, len(wf.steps))
        self.assertEqual("two", wf.steps[0].id)

        # non-existing name
        self.assertRaises(
            SystemExit,
            WorkflowParser.parse,
            **{"wf_data": wf_data, "skipped_steps": ["four"]}
        )

        # skip one step
        wf = WorkflowParser.parse(wf_data=wf_data, skipped_steps=["two"])
        self.assertEqual(2, len(wf.steps))
        self.assertEqual("one", wf.steps[0].id)
        self.assertEqual("three", wf.steps[1].id)

        # without id
        wf_data = {"steps": [{"uses": "foo"}, {"uses": "bar"}, {"uses": "baz"},]}
        wf = WorkflowParser.parse(wf_data=wf_data, skipped_steps=["1", "3"])
        self.assertEqual(1, len(wf.steps))
        self.assertEqual("2", wf.steps[0].id)

    def test_add_missing_ids(self):
        wf_data = {"steps": [{"uses": "foo"}, {"uses": "bar"}]}
        # skip one step
        wf = WorkflowParser.parse(wf_data=wf_data)
        self.assertEqual("1", wf.steps[0].id)
        self.assertEqual("2", wf.steps[1].id)

    def test_substitutions(self):
        # test wrong format for substitution key
        wf_data = {"steps": [{"uses": "whatever"}]}
        self.assertRaises(
            SystemExit,
            WorkflowParser.parse,
            **{"wf_data": wf_data, "substitutions": ["SUB1=WRONG"]}
        )

        # expect error when not all given subs are used
        wf_data = {
            "steps": [
                {
                    "uses": "some_$_SUB1",
                    "id": "some other $_SUB2",
                    "env": {"FOO": "env_$_SUB3"},
                    "secrets": ["secret_$_SUB4"],
                }
            ]
        }
        substitutions = [
            "_SUB1=ONE",
            "_SUB2=TWO",
            "_SUB3=THREE",
            "_SUB4=4",
            "_SUB5=UNUSED",
        ]
        self.assertRaises(
            SystemExit,
            WorkflowParser.parse,
            **{"wf_data": wf_data, "substitutions": substitutions}
        )

        # allow loose substitutions
        wf = WorkflowParser.parse(
            wf_data=wf_data, substitutions=substitutions, allow_loose=True
        )
        step = wf.steps[0]
        self.assertEqual("some_ONE", step.uses)
        self.assertEqual("some other TWO", step.id)
        self.assertEqual("env_THREE", step.env["FOO"])
        self.assertEqual(("secret_4",), step.secrets)
