import unittest
import os
import shutil

from popper.parser import Workflow
from popper.cli import log


class TestParser(unittest.TestCase):

    def setUp(self):
        os.makedirs('/tmp/test_folder')
        os.chdir('/tmp/test_folder')
        log.setLevel('CRITICAL')

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        log.setLevel('NOTSET')

    def create_workflow_file(self, content):
        f = open('/tmp/test_folder/a.workflow', 'w')
        f.write(content)
        f.close()

    def test_check_for_empty_workflow(self):
        self.create_workflow_file("""
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
        workflow = Workflow('/tmp/test_folder/a.workflow')
        workflow.normalize()
        workflow.resolves = ["a1", "a2"]
        self.assertRaises(SystemExit, workflow.check_for_empty_workflow)

    def test_format_command(self):
        cmd = u"docker version"
        res = Workflow.format_command(cmd)
        self.assertEqual(res, ["docker", "version"])

        cmd = ["docker", "version"]
        res = Workflow.format_command(cmd)
        self.assertEqual(res, ["docker", "version"])

    def test_check_duplicate_actions(self):
        self.create_workflow_file("""
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
        workflow = Workflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, workflow.check_duplicate_actions)

        self.create_workflow_file("""
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

        workflow = Workflow('/tmp/test_folder/a.workflow')
        workflow.check_duplicate_actions()

    def test_validate_workflow_block(self):
        self.create_workflow_file("""
        workflow "sample workflow 1" {
            resolves = ["a"]
        }

        workflow "sample workflow 2" {
            resolves = ["a"]
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_workflow_block)

        self.create_workflow_file("""
        action "a" {
            uses = "sh"
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_workflow_block)

        self.create_workflow_file("""
        workflow "sample workflow 1" {
            resolves = ["a"]
            runs = ["sh", "-c", "ls"]
        }

        action "a" {
            uses = ["sh"]
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_workflow_block)

        self.create_workflow_file("""
        workflow "sample workflow 1" {
            on = "push"
        }

        action "a" {
            uses = ["sh"]
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_workflow_block)

    def test_validate_action_blocks(self):
        self.create_workflow_file("""
        workflow "sample workflow" {
            resolves = "a"
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        self.create_workflow_file("""
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            uses = "sh"
            on = "push"
        }
        """)

        wf = Workflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        self.create_workflow_file("""
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            args = "ls"
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        self.create_workflow_file("""
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            uses = 1
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        self.create_workflow_file("""
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            uses = "sh"
            needs = 1
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        self.create_workflow_file("""
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            uses = "sh"
            args = [1, 2, 3, 4]
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        self.create_workflow_file("""
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            uses = "sh"
            runs = [1, 2, 3, 4]
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        self.create_workflow_file("""
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
        wf = Workflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

        self.create_workflow_file("""
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
        wf = Workflow('/tmp/test_folder/a.workflow')
        self.assertRaises(SystemExit, wf.validate_action_blocks)

    def test_normalize(self):
        self.create_workflow_file("""
        workflow "sample workflow" {
            resolves = "a"
        }

        action "a" {
            needs = "b"
            uses = "actions/bin/npm@master"
            args = "npm --version"
            secrets = "SECRET_KEY"
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        wf.normalize()
        self.assertEqual(wf.resolves, ['a'])
        self.assertEqual(wf.name, 'sample workflow')
        self.assertEqual(wf.on, 'push')
        self.assertDictEqual(wf.props, dict())
        action_a = wf.get_action('a')
        self.assertEqual(action_a['name'], 'a')
        self.assertEqual(action_a['needs'], ['b'])
        self.assertEqual(action_a['args'], ['npm', '--version'])
        self.assertEqual(action_a['secrets'], ['SECRET_KEY'])

    def test_complete_graph(self):
        self.create_workflow_file("""
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
        wf = Workflow('/tmp/test_folder/a.workflow')
        wf.normalize()
        wf.complete_graph()
        self.assertEqual(wf.name, 'example')
        self.assertEqual(wf.resolves, ['end'])
        self.assertEqual(wf.on, 'push')
        self.assertEqual(wf.props, {})
        self.assertEqual(wf.root, {'b', 'c', 'a'})

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
        self.assertDictEqual(wf.action, actions_dict)

    def test_skip_actions(self):
        self.create_workflow_file("""
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
        wf = Workflow('/tmp/test_folder/a.workflow')
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
        self.create_workflow_file("""
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
        wf = Workflow('/tmp/test_folder/a.workflow')
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

    def test_check_for_unreachable_actions(self):
        self.create_workflow_file("""
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
        wf = Workflow('/tmp/test_folder/a.workflow')
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

        self.create_workflow_file("""
        workflow "sample" {
            resolves = ["reachable"]
        }

        action "reachable" {
            uses = "actions/bin/sh@master"
            args = "ls"
        }

        action "unreachable" {
            uses = "actions/bin/sh@master"
            args = ["ls -ltr"]
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        wf.parse()
        wf.check_for_unreachable_actions()

    def test_get_stages(self):
        self.create_workflow_file("""
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
        wf = Workflow('/tmp/test_folder/a.workflow')
        wf.parse()
        stages = list()
        for stage in wf.get_stages():
            stages.append(stage)

        self.assertListEqual(stages, [
            {'b', 'c', 'a'},
            {'d'},
            {'e'},
            {'end'}
        ])

        self.create_workflow_file("""
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
        wf = Workflow('/tmp/test_folder/a.workflow')
        wf.parse()
        stages = list()
        for stage in wf.get_stages():
            stages.append(stage)

        self.assertListEqual(stages, [
            {'a', 'c'},
            {'b'},
            {'d'},
            {'g', 'f'},
            {'h'},
            {'end'}
        ])
