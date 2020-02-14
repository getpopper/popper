import unittest
import os
import shutil

from popper.parser import Workflow, YMLWorkflow, HCLWorkflow
from popper.cli import log
from popper import utils as pu


class TestWorkflow(unittest.TestCase):
    def setUp(self):
        os.makedirs('/tmp/test_folder')
        os.chdir('/tmp/test_folder')
        log.setLevel('CRITICAL')

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        log.setLevel('NOTSET')

    def test_verify_action(self):
        pu.write_file('/tmp/test_folder/a.yml', """
        steps:
        - id: 'a'
          uses: 'sh'

        - id: 'b'
          needs: 'a1'
          uses: 'sh'
        """)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample" {
            resolves = ["a", "b"]
        }

        action "a" {
            uses = "sh"
        }

        action "b" {
            needs = "a1"
            uses = "sh"
        }
        """)

        yml_workflow = YMLWorkflow('/tmp/test_folder/a.yml')
        hcl_workflow = HCLWorkflow('/tmp/test_folder/a.workflow')

        yml_workflow.normalize()
        hcl_workflow.normalize()

        self.assertEqual(yml_workflow.verify_action('c'), False)
        self.assertEqual(yml_workflow.verify_action('a'), True)

        self.assertEqual(hcl_workflow.verify_action('c'), False)
        self.assertEqual(hcl_workflow.verify_action('a'), True)

    def test_check_for_broken_workflow(self):
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "samples" {
            resolves = ["a1", "a2"]
        }

        action "b" {
            uses = "sh"
        }

        action "c" {
            uses = "sh"
        }
        """)

        pu.write_file('/tmp/test_folder/a.yml', """
        steps:
        - id: 'a'
          uses: 'sh'

        - id: 'b'
          needs: 'a1'
          uses: 'sh'
        """)

        hcl_workflow = HCLWorkflow('/tmp/test_folder/a.workflow')
        yml_workflow = YMLWorkflow('/tmp/test_folder/a.yml')

        hcl_workflow.normalize()
        yml_workflow.normalize()

        hcl_workflow.resolves = ["a1", "a2"]
        self.assertRaises(SystemExit, hcl_workflow.check_for_broken_workflow)
        self.assertRaises(SystemExit, yml_workflow.check_for_broken_workflow)

    def test_format_command(self):
        cmd = u"docker version"
        res = Workflow.format_command(cmd)
        self.assertEqual(res, ["docker", "version"])

        cmd = ["docker", "version"]
        res = Workflow.format_command(cmd)
        self.assertEqual(res, ["docker", "version"])

    def test_check_duplicate_actions(self):
        pu.write_file('/tmp/test_folder/a.yml', """
        steps:
        - id: 'a'
          uses: 'sh'

        - id: 'b'
          uses: 'sh'

        - id: 'a'
          uses: 'sh'
        """)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample" {
            resolves = ["a", "b"]
        }

        action "a" {
            uses = "sh"
        }

        action "b" {
            uses = "sh"
        }

        action "a" {
            uses = "sh"
        }
        """)

        yml_workflow = YMLWorkflow('/tmp/test_folder/a.yml')
        hcl_workflow = HCLWorkflow('/tmp/test_folder/a.workflow')

        self.assertRaises(SystemExit, yml_workflow.check_duplicate_actions)
        self.assertRaises(SystemExit, hcl_workflow.check_duplicate_actions)

        pu.write_file('/tmp/test_folder/a.yml', """
        steps:
        - id: 'a'
          uses: 'sh'

        - id: 'b'
          uses: 'sh'
        """)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample" {
            resolves = ["a", "b"]
        }

        action "a" {
            uses = "sh"
        }

        action "b" {
            uses = "sh"
        }
        """)

        yml_workflow = YMLWorkflow('/tmp/test_folder/a.yml')
        hcl_workflow = HCLWorkflow('/tmp/test_folder/a.workflow')

        yml_workflow.check_duplicate_actions()
        hcl_workflow.check_duplicate_actions()

    def test_validate_workflow_block(self):
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample workflow 1" {
            resolves = ["a"]
        }

        workflow "sample workflow 2" {
            resolves = ["a"]
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_workflow_block)

        pu.write_file('/tmp/test_folder/a.workflow', """
        action "a" {
            uses = "sh"
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_workflow_block)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample workflow 1" {
            resolves = ["a"]
            runs = ["sh", "-c", "ls"]
        }

        action "a" {
            uses = ["sh"]
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_workflow_block)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample workflow 1" {
            on = "push"
        }

        action "a" {
            uses = ["sh"]
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_workflow_block)

    def test_validate_action_blocks(self):
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample workflow" {
            resolves = "a"
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            uses = "sh"
            on = "push"
        }
        """)

        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            args = "ls"
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            uses = 1
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            uses = "sh"
            needs = 1
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            uses = "sh"
            args = [1, 2, 3, 4]
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            uses = "sh"
            runs = [1, 2, 3, 4]
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            uses = "sh"
            secrets = {
                SECRET_A = 1234,
                SECRET_B =  5678
            }
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            uses = "sh"
            env = [
                "SECRET_A", "SECRET_B"
            ]
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

    def test_skip_actions(self):
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "example" {
            resolves = "end"
            }

            action "a" {
            uses = "sh"
            args = "ls"
            }

            action "b" {
            uses = "sh"
            args = "ls"
            }

            action "c" {
            uses = "sh"
            args = "ls"
            }

            action "d" {
            needs = ["c"]
            uses = "sh"
            args = "ls"
            }

            action "e" {
            needs = ["d", "b", "a"]
            uses = "sh"
            args = "ls"
            }

            action "end" {
            needs = "e"
            uses = "sh"
            args = "ls"
            }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        wf.parse()
        changed_wf = Workflow.skip_actions(wf, ['b'])
        self.assertDictEqual(changed_wf.action, {
            'a': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'a',
                'next': {'e'}},
            'b': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'b',
                'next': set()},
            'c': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'c',
                'next': {'d'}},
            'd': {
                'needs': ['c'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'd',
                'next': {'e'}},
            'e': {
                'needs': ['d', 'a'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'e',
                'next': {'end'}},
            'end': {
                'needs': ['e'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'end'}})

        changed_wf = Workflow.skip_actions(wf, ['d', 'a'])
        self.assertDictEqual(changed_wf.action, {
            'a': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'a',
                'next': set()},
            'b': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'b',
                'next': {'e'}},
            'c': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'c',
                'next': set()},
            'd': {
                'needs': [],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'd',
                'next': set()},
            'e': {
                'needs': ['b'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'e',
                'next': {'end'}},
            'end': {
                'needs': ['e'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'end'}})

    def test_filter_action(self):
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "example" {
            resolves = "end"
            }

            action "a" {
            uses = "sh"
            args = "ls"
            }

            action "b" {
            uses = "sh"
            args = "ls"
            }

            action "c" {
            uses = "sh"
            args = "ls"
            }

            action "d" {
            needs = ["c"]
            uses = "sh"
            args = "ls"
            }

            action "e" {
            needs = ["d", "b", "a"]
            uses = "sh"
            args = "ls"
            }

            action "end" {
            needs = "e"
            uses = "sh"
            args = "ls"
            }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        wf.parse()
        changed_wf = Workflow.filter_action(wf, 'e')
        self.assertSetEqual(changed_wf.root, {'e'})
        self.assertDictEqual(
            changed_wf.action, {
                'e': {
                    'needs': [],
                    'uses': 'sh',
                    'args': ['ls'],
                    'name': 'e',
                    'next': set()}})

        changed_wf = Workflow.filter_action(wf, 'd')
        self.assertSetEqual(changed_wf.root, {'d'})
        self.assertDictEqual(
            changed_wf.action, {
                'd': {
                    'needs': [],
                    'uses': 'sh',
                    'args': ['ls'],
                    'name': 'd',
                    'next': set()}})

        changed_wf = Workflow.filter_action(wf, 'e', with_dependencies=True)
        self.assertSetEqual(changed_wf.root, {'b', 'a', 'c'})
        self.assertDictEqual(changed_wf.action, {
            'a': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'a',
                'next': {'e'}},
            'b': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'b',
                'next': {'e'}},
            'c': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'c',
                'next': {'d'}},
            'd': {
                'needs': ['c'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'd',
                'next': {'e'}},
            'e': {
                'needs': ['d', 'b', 'a'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'e',
                'next': set()}})

        changed_wf = Workflow.filter_action(wf, 'd', with_dependencies=True)
        self.assertSetEqual(changed_wf.root, {'c'})
        self.assertDictEqual(
            changed_wf.action, {
                'c': {
                    'uses': 'sh',
                    'args': ['ls'],
                    'name': 'c',
                    'next': {'d'}},
                'd': {
                    'needs': ['c'],
                    'uses': 'sh',
                    'args': ['ls'],
                    'name': 'd',
                    'next': set()}})

        pu.write_file('/tmp/test_folder/a.yml', """
        steps:
        - id: "a"
          uses: "sh"
          args: "ls"

        - id: "b"
          uses: "sh"
          args: "ls"

        - id: "c"
          uses: "sh"
          args: "ls"

        - id: "d"
          needs: ["c"]
          uses: "sh"
          args: "ls"

        - id: "e"
          needs: ["d", "b", "a"]
          uses: "sh"
          args: "ls"

        - id: "end"
          needs: "e"
          uses: "sh"
          args: "ls"
        """)

        wf = YMLWorkflow('/tmp/test_folder/a.yml')
        wf.parse()
        changed_wf = Workflow.filter_action(wf, 'e')
        self.assertSetEqual(changed_wf.root, {'e'})
        self.assertDictEqual(
            changed_wf.action, {
                'e': {
                    'id': 'e',
                    'needs': [],
                    'uses': 'sh',
                    'args': ['ls'],
                    'name': 'e',
                    'next': set()}})

        changed_wf = Workflow.filter_action(wf, 'd')
        self.assertSetEqual(changed_wf.root, {'d'})
        self.assertDictEqual(
            changed_wf.action, {
                'd': {
                    'id': 'd',
                    'needs': [],
                    'uses': 'sh',
                    'args': ['ls'],
                    'name': 'd',
                    'next': set()}})

        changed_wf = Workflow.filter_action(wf, 'e', with_dependencies=True)
        self.assertSetEqual(changed_wf.root, {'b', 'a', 'c'})
        self.assertDictEqual(changed_wf.action, {
            'a': {
                'id': 'a',
                'uses': 'sh',
                'args': ['ls'],
                'name': 'a',
                'next': {'e'}},
            'b': {
                'id': 'b',
                'uses': 'sh',
                'args': ['ls'],
                'name': 'b',
                'next': {'e'}},
            'c': {
                'id': 'c',
                'uses': 'sh',
                'args': ['ls'],
                'name': 'c',
                'next': {'d'}},
            'd': {
                'id': 'd',
                'needs': ['c'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'd',
                'next': {'e'}},
            'e': {
                'id': 'e',
                'needs': ['d', 'b', 'a'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'e',
                'next': set()}})

        changed_wf = Workflow.filter_action(wf, 'd', with_dependencies=True)
        self.assertSetEqual(changed_wf.root, {'c'})
        self.assertDictEqual(
            changed_wf.action, {
                'c': {
                    'id': 'c',
                    'uses': 'sh',
                    'args': ['ls'],
                    'name': 'c',
                    'next': {'d'}},
                'd': {
                    'id': 'd',
                    'needs': ['c'],
                    'uses': 'sh',
                    'args': ['ls'],
                    'name': 'd',
                    'next': set()}})

    def test_check_for_unreachable_actions(self):
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "example" {
        resolves = "end"
        }

        action "a" {
        uses = "sh"
        args = "ls"
        }

        action "b" {
        uses = "sh"
        args = "ls"
        }

        action "c" {
        uses = "sh"
        args = "ls"
        }

        action "d" {
        needs = ["c"]
        uses = "sh"
        args = "ls"
        }

        action "e" {
        needs = ["d", "b", "a"]
        uses = "sh"
        args = "ls"
        }

        action "end" {
        needs = "e"
        uses = "sh"
        args = "ls"
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        wf.parse()
        changed_wf = Workflow.skip_actions(wf, ['d', 'a', 'b'])
        self.assertDictEqual(changed_wf.action, {
            'a': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'a',
                'next': set()},
            'b': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'b',
                'next': set()},
            'c': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'c',
                'next': set()},
            'd': {
                'needs': [],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'd',
                'next': set()},
            'e': {
                'needs': [],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'e',
                'next': {'end'}},
            'end': {
                'needs': ['e'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'end'}
        })
        self.assertRaises(
            SystemExit,
            changed_wf.check_for_unreachable_actions,
            True)

        pu.write_file('/tmp/test_folder/a.yml', """
        steps:
        - id: "reachable"
          uses: "popperized/bin/sh@master"
          args: "ls"

        - id: "unreachable"
          uses: "popperized/bin/sh@master"
          args: ["ls -ltr"]
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        wf.parse()
        wf.check_for_unreachable_actions()

    def test_get_stages(self):
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "example" {
        resolves = "end"
        }

        action "a" {
        uses = "sh"
        args = "ls"
        }

        action "b" {
        uses = "sh"
        args = "ls"
        }

        action "c" {
        uses = "sh"
        args = "ls"
        }

        action "d" {
        needs = ["c"]
        uses = "sh"
        args = "ls"
        }

        action "e" {
        needs = ["d", "b", "a"]
        uses = "sh"
        args = "ls"
        }

        action "end" {
        needs = "e"
        uses = "sh"
        args = "ls"
        }
        """)
        hcl_workflow = HCLWorkflow('/tmp/test_folder/a.workflow')
        hcl_workflow.parse()
        stages = list()
        for stage in hcl_workflow.get_stages():
            stages.append(stage)

        self.assertListEqual(stages, [
            {'b', 'c', 'a'},
            {'d'},
            {'e'},
            {'end'}
        ])

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "example" {
            resolves = ["end"]
        }

        action "a" {
            uses = "sh"
            args = "ls"
        }

        action "b" {
            needs = "a"
            uses = "sh"
            args = "ls"
        }

        action "c" {
            uses = "sh"
            args = "ls"
        }

        action "d" {
            uses = "sh"
            needs = ["b", "c"]
            args = "ls"
        }

        action "g" {
            needs = "d"
            uses = "sh"
            args = "ls"
        }

        action "f" {
            needs = "d"
            uses = "sh"
            args = "ls"
        }

        action "h" {
            needs = "g"
            uses = "sh"
            args = "ls"
        }

        action "end" {
            needs = ["h", "f"]
            uses = "sh"
            args = "ls"
        }
        """)
        hcl_workflow = HCLWorkflow('/tmp/test_folder/a.workflow')
        hcl_workflow.parse()
        stages = list()
        for stage in hcl_workflow.get_stages():
            stages.append(stage)

        self.assertListEqual(stages, [
            {'a', 'c'},
            {'b'},
            {'d'},
            {'g', 'f'},
            {'h'},
            {'end'}
        ])

        pu.write_file('/tmp/test_folder/a.yml', """
        steps:
        - id: "a"
          uses: "sh"
          args: "ls"

        - id: "b"
          uses: "sh"
          args: "ls"

        - id: "c"
          uses: "sh"
          args: "ls"

        - id: "d"
          needs: ["c"]
          uses: "sh"
          args: "ls"

        - id: "e"
          needs: ["d", "b", "a"]
          uses: "sh"
          args: "ls"

        - id: "end"
          needs: "e"
          uses: "sh"
          args: "ls"
        """)

        yml_workflow = YMLWorkflow('/tmp/test_folder/a.yml')
        yml_workflow.parse()
        stages = list()
        for stage in yml_workflow.get_stages():
            stages.append(stage)

        self.assertListEqual(stages, [
            {'b', 'c', 'a'},
            {'d'},
            {'e'},
            {'end'}
        ])

        pu.write_file('/tmp/test_folder/a.yml', """
        steps:
        - id: "a"
          uses: "sh"
          args: "ls"

        - id: "b"
          needs: "a"
          uses: "sh"
          args: "ls"

        - id: "c"
          uses: "sh"
          args: "ls"

        - id: "d"
          uses: "sh"
          needs: ["b", "c"]
          args: "ls"

        - id: "g"
          needs: "d"
          uses: "sh"
          args: "ls"

        - id: "f"
          needs: "d"
          uses: "sh"
          args: "ls"

        - id: "h"
          needs: "g"
          uses: "sh"
          args: "ls"

        - id: "end"
          needs: ["h", "f"]
          uses: "sh"
          args: "ls"
        """)
        yml_workflow = YMLWorkflow('/tmp/test_folder/a.yml')
        yml_workflow.parse()
        stages = list()
        for stage in yml_workflow.get_stages():
            stages.append(stage)

        self.assertListEqual(stages, [
            {'a', 'c'},
            {'b'},
            {'d'},
            {'g', 'f'},
            {'h'},
            {'end'}
        ])

    def test_substitutions(self):
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "example" {
            resolves = ["b"]
        }

        action "a" {
            uses = "$_VAR1"
            args = "$_VAR2"
        }

        action "b" {
            needs = "$_VAR3"
            uses = "$_VAR1"
            args = "$_VAR2"
            runs = "$_VAR4"
            secrets = ["$_VAR5"]
            env = {
                "$_VAR6" = "$_VAR7"
            }
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow',
                         ['_VAR1=sh', '_VAR2=ls', '_VAR3=a',
                          '_VAR4=test_env', '_VAR5=TESTING',
                          '_VAR6=TESTER', '_VAR7=TEST'], False)
        wf.parse()
        self.assertDictEqual(wf.action, {
            'a': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'a',
                'next': {'b'}},
            'b': {
                'needs': ['a'],
                'uses': 'sh',
                'args': ['ls'],
                'runs': ['test_env'],
                'secrets': ['TESTING'],
                'env': {
                    'TESTER': 'TEST'
                },
                'name': 'b'}
        })

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "example" {
            resolves = ["b"]
        }

        action "a" {
            uses = "$_VAR1"
            args = "$_VAR2"
        }

        action "b" {
            needs = "$_VAR3"
            uses = "$_VAR1"
            args = "$_VAR2"
            runs = "$_VAR4"
            secrets = ["$_VAR5"]
            env = {
                "$_VAR6" = "$_VAR7"
            }
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow',
                         ['_VAR1=sh', '_VAR2=ls', '_VAR3=a',
                          '_VAR4=test_env', '_VAR5=TESTING',
                          '_VAR6=TESTER', '_VAR7=TEST', '_VAR8=sd'], True)
        wf.parse()
        self.assertDictEqual(wf.action, {
            'a': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'a',
                'next': {'b'}},
            'b': {
                'needs': ['a'],
                'uses': 'sh',
                'args': ['ls'],
                'runs': ['test_env'],
                'secrets': ['TESTING'],
                'env': {
                    'TESTER': 'TEST'
                },
                'name': 'b'}
        })


class TestHCLWorkflow(unittest.TestCase):
    def setUp(self):
        os.makedirs('/tmp/test_folder')
        os.chdir('/tmp/test_folder')
        log.setLevel('CRITICAL')

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        log.setLevel('NOTSET')

    def test_load_file(self):
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample" {
            resolves = "b"
        }

        action "a" {
            uses = "sh"
        }

        action "b" {
            needs = "a"
            uses = "sh"
        }
        """)
        hcl_workflow = HCLWorkflow('/tmp/test_folder/a.workflow')
        hcl_workflow.load_file()
        self.assertEqual(hcl_workflow.wf_fmt, "hcl")
        self.assertDictEqual(
            hcl_workflow.wf_dict, {
                'workflow': {
                    'sample': {
                        'resolves': 'b'}}, 'action': {
                    'a': {
                        'uses': 'sh'}, 'b': {
                            'needs': 'a', 'uses': 'sh'}}})

    def test_normalize(self):
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            needs = "b"
            uses = "popperized/bin/npm@master"
            args = "npm --version"
            secrets = "SECRET_KEY"
        }
        """)
        hcl_workflow = HCLWorkflow('/tmp/test_folder/a.workflow')
        hcl_workflow.normalize()
        self.assertEqual(hcl_workflow.resolves, ['a'])
        self.assertEqual(hcl_workflow.name, 'sample workflow')
        self.assertEqual(hcl_workflow.on, 'push')
        self.assertDictEqual(hcl_workflow.props, dict())
        action_a = hcl_workflow.action['a']
        self.assertEqual(action_a['name'], 'a')
        self.assertEqual(action_a['needs'], ['b'])
        self.assertEqual(action_a['args'], ['npm', '--version'])
        self.assertEqual(action_a['secrets'], ['SECRET_KEY'])

    def test_complete_graph(self):
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "example" {
        resolves = "end"
        }

        action "a" {
        uses = "sh"
        args = "ls"
        }

        action "b" {
        uses = "sh"
        args = "ls"
        }

        action "c" {
        uses = "sh"
        args = "ls"
        }

        action "d" {
        needs = ["c"]
        uses = "sh"
        args = "ls"
        }

        action "e" {
        needs = ["d", "b", "a"]
        uses = "sh"
        args = "ls"
        }

        action "end" {
        needs = "e"
        uses = "sh"
        args = "ls"
        }
        """)
        hcl_workflow = HCLWorkflow('/tmp/test_folder/a.workflow')
        hcl_workflow.normalize()
        hcl_workflow.complete_graph()
        self.assertEqual(hcl_workflow.name, 'example')
        self.assertEqual(hcl_workflow.resolves, ['end'])
        self.assertEqual(hcl_workflow.on, 'push')
        self.assertEqual(hcl_workflow.props, {})
        self.assertEqual(hcl_workflow.root, {'b', 'c', 'a'})

        actions_dict = {
            'a': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'a',
                'next': {'e'}},
            'b': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'b',
                'next': {'e'}},
            'c': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'c',
                'next': {'d'}},
            'd': {
                'needs': ['c'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'd',
                'next': {'e'}},
            'e': {
                'needs': ['d', 'b', 'a'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'e',
                'next': {'end'}},
            'end': {
                'needs': ['e'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'end'}
        }
        self.assertDictEqual(hcl_workflow.action, actions_dict)


class TestYMLWorkflow(unittest.TestCase):
    def setUp(self):
        os.makedirs('/tmp/test_folder')
        os.chdir('/tmp/test_folder')
        log.setLevel('CRITICAL')

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        log.setLevel('NOTSET')

    def test_load_file(self):
        pu.write_file('/tmp/test_folder/a.yml', """
        steps:
        - id: 'a'
          uses: 'sh'

        - id: 'b'
          uses: 'sh'
        """)
        yml_workflow = YMLWorkflow('/tmp/test_folder/a.yml')
        yml_workflow.load_file()
        self.assertEqual(yml_workflow.wf_fmt, "yml")
        self.assertDictEqual(
            yml_workflow.wf_dict, {
                'action': {
                    'a': {
                        'id': 'a', 'uses': 'sh'}, 'b': {
                        'id': 'b', 'uses': 'sh'}}})
        self.assertListEqual(
            yml_workflow.wf_list,
            [{'id': 'a', 'uses': 'sh'}, {'id': 'b', 'uses': 'sh'}])
        self.assertDictEqual(
            yml_workflow.id_map,
            {1: 'a', 2: 'b'})

    def test_normalize(self):
        pu.write_file('/tmp/test_folder/a.yml', """
        steps:
        - id: "a"
          needs: "b"
          uses: "popperized/bin/npm@master"
          args: "npm --version"
          secrets: "SECRET_KEY"
        """)
        yml_workflow = YMLWorkflow('/tmp/test_folder/a.yml')
        yml_workflow.normalize()
        self.assertEqual(yml_workflow.name, 'a')
        self.assertEqual(yml_workflow.on, '')
        self.assertDictEqual(yml_workflow.props, dict())
        action_a = yml_workflow.action['a']
        self.assertEqual(action_a['name'], 'a')
        self.assertEqual(action_a['needs'], ['b'])
        self.assertEqual(action_a['args'], ['npm', '--version'])
        self.assertEqual(action_a['secrets'], ['SECRET_KEY'])

    def test_complete_graph(self):
        pu.write_file('/tmp/test_folder/a.yml', """
        steps:
        - id: 'a'
          uses: 'sh'
          args: 'ls'

        - id: 'b'
          uses: 'sh'
          args: 'ls'

        - id: 'c'
          uses: 'sh'
          args: 'ls'

        - id: 'd'
          needs: 'c'
          uses: 'sh'
          args: 'ls'

        - id: 'e'
          needs: ['d', 'b', 'a']
          uses: 'sh'
          args: 'ls'

        - id: 'end'
          needs: 'e'
          uses: 'sh'
          args: 'ls'
        """)
        yml_workflow = YMLWorkflow('/tmp/test_folder/a.yml')
        yml_workflow.normalize()
        yml_workflow.complete_graph()
        self.assertEqual(yml_workflow.name, 'a')
        self.assertEqual(yml_workflow.on, '')
        self.assertEqual(yml_workflow.props, {})
        self.assertEqual(yml_workflow.root, {'b', 'c', 'a'})

        actions_dict = {
            'a': {
                'id': 'a',
                'uses': 'sh',
                'args': ['ls'],
                'name': 'a',
                'next': {'e'}
            },
            'b': {
                'id': 'b',
                'uses': 'sh',
                'args': ['ls'],
                'name': 'b',
                'next': {'e'}
            },
            'c': {
                'id': 'c',
                'uses': 'sh',
                'args': ['ls'],
                'name': 'c',
                'next': {'d'}
            }, 'd': {
                'id': 'd',
                'needs': ['c'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'd',
                'next': {'e'}
            }, 'e': {
                'id': 'e',
                'needs': ['d', 'b', 'a'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'e',
                'next': {'end'}
            }, 'end': {
                'id': 'end',
                'needs': ['e'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'end'}
        }
        self.assertDictEqual(yml_workflow.action, actions_dict)
