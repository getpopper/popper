import unittest
import os

from popper.parser import Workflow, YMLWorkflow, HCLWorkflow
from popper.cli import log

FIXDIR = f'{os.path.dirname(os.path.realpath(__file__))}/fixtures'


def _wfile(name, format):
    return f'{FIXDIR}/{name}.{format}'


class TestWorkflow(unittest.TestCase):
    def setUp(self):
        log.setLevel('CRITICAL')

    def tearDown(self):
        log.setLevel('NOTSET')

    def test_new_workflow(self):
        self.assertIsInstance(
            Workflow.new(_wfile('a', 'yml')), YMLWorkflow)
        self.assertIsInstance(
            Workflow.new(_wfile('a', 'workflow')), HCLWorkflow)

    def test_missing_dependency(self):
        wf = HCLWorkflow(_wfile('missing_dependency', 'workflow'))
        wf.normalize()
        self.assertRaises(SystemExit, wf.check_for_broken_workflow)
        wf = YMLWorkflow(_wfile('missing_dependency', 'yml'))
        wf.normalize()
        self.assertRaises(SystemExit, wf.check_for_broken_workflow)

    def test_command(self):
        cmd = u"docker version"
        res = Workflow.format_command(cmd)
        self.assertEqual(res, ["docker", "version"])

        cmd = ["docker", "version"]
        res = Workflow.format_command(cmd)
        self.assertEqual(res, ["docker", "version"])

    def test_validate_workflow_block(self):
        wf = HCLWorkflow("""workflow "w1" {
    resolves = ["a"]
}
workflow "w2" {
    resolves = ["a"]
}
""")
        self.assertRaises(SystemExit, wf.validate_workflow_block)

        wf = HCLWorkflow("""
action "a" {
    uses = "sh"
}
""")
        self.assertRaises(SystemExit, wf.validate_workflow_block)

        wf = HCLWorkflow("""
workflow "sample workflow 1" {
    resolves = ["a"]
    runs = ["sh", "-c", "ls"]
}
action "a" {
    uses = ["sh"]
}
""")
        self.assertRaises(SystemExit, wf.validate_workflow_block)

        wf = HCLWorkflow("""
workflow "sample workflow 1" {
    on = "push"
}
action "a" {
    uses = ["sh"]
}
""")
        self.assertRaises(SystemExit, wf.validate_workflow_block)

    def test_validate_step_blocks(self):
        wf = HCLWorkflow("""workflow "sample workflow" {
            resolves = "a"
        }""")
        self.assertRaises(SystemExit, wf.validate_step_blocks)

        wf = HCLWorkflow("""workflow "sample workflow" {
    resolves = "a"
}
action "a" {
    uses = "sh"
    on = "push"
}""")
        self.assertRaises(SystemExit, wf.validate_step_blocks)

        wf = HCLWorkflow("""workflow "sample workflow" {
    resolves = "a"
}
action "a" {
    args = "ls"
}""")
        self.assertRaises(SystemExit, wf.validate_step_blocks)

        wf = HCLWorkflow("""workflow "sample workflow" {
    resolves = "a"
}
action "a" {
    uses = 1
}""")
        self.assertRaises(SystemExit, wf.validate_step_blocks)

        wf = HCLWorkflow("""workflow "sample workflow" {
    resolves = "a"
}

action "a" {
    uses = "sh"
    needs = 1
}""")
        self.assertRaises(SystemExit, wf.validate_step_blocks)

        wf = HCLWorkflow("""workflow "sample workflow" {
    resolves = "a"
}
action "a" {
    uses = "sh"
    args = [1, 2, 3, 4]
}
""")
        self.assertRaises(SystemExit, wf.validate_step_blocks)

        wf = HCLWorkflow("""workflow "sample workflow" {
    resolves = "a"
}
action "a" {
    uses = "sh"
    runs = [1, 2, 3, 4]
}
""")
        self.assertRaises(SystemExit, wf.validate_step_blocks)

        wf = HCLWorkflow("""workflow "sample workflow" {
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
        self.assertRaises(SystemExit, wf.validate_step_blocks)

        wf = HCLWorkflow("""workflow "sample workflow" {
    resolves = "a"
}
action "a" {
    uses = "sh"
    env = [
        "SECRET_A", "SECRET_B"
    ]
}
""")
        self.assertRaises(SystemExit, wf.validate_step_blocks)

    def test_skip_steps(self):
        wf = YMLWorkflow(_wfile('a', 'yml'))
        wf.parse()
        changed_wf = Workflow.skip_steps(wf, ['b'])
        self.assertDictEqual(changed_wf.steps, {
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

        changed_wf = Workflow.skip_steps(wf, ['d', 'a'])
        self.assertDictEqual(changed_wf.steps, {
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

    def test_filter_step(self):
        wf = YMLWorkflow(_wfile('a', 'yml'))
        wf.parse()
        changed_wf = Workflow.filter_step(wf, 'e')
        self.assertSetEqual(changed_wf.root, {'e'})
        self.assertDictEqual(
            changed_wf.steps, {
                'e': {
                    'needs': [],
                    'uses': 'sh',
                    'args': ['ls'],
                    'name': 'e',
                    'next': set()}})

        changed_wf = Workflow.filter_step(wf, 'd')
        self.assertSetEqual(changed_wf.root, {'d'})
        self.assertDictEqual(
            changed_wf.steps, {
                'd': {
                    'needs': [],
                    'uses': 'sh',
                    'args': ['ls'],
                    'name': 'd',
                    'next': set()}})

        changed_wf = Workflow.filter_step(wf, 'e', with_dependencies=True)
        self.assertSetEqual(changed_wf.root, {'b', 'a', 'c'})
        self.assertDictEqual(changed_wf.steps, {
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

        changed_wf = Workflow.filter_step(wf, 'd', with_dependencies=True)
        self.assertSetEqual(changed_wf.root, {'c'})
        self.assertDictEqual(
            changed_wf.steps, {
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

    def test_check_for_unreachable_steps(self):
        wf = HCLWorkflow(_wfile('a', 'workflow'))
        wf.parse()
        changed_wf = Workflow.skip_steps(wf, ['d', 'a', 'b'])
        self.assertDictEqual(changed_wf.steps, {
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

        changed_wf.check_for_unreachable_steps()

        wf = HCLWorkflow(_wfile('ok', 'workflow'))
        wf.parse()
        wf.check_for_unreachable_steps()

    def test_get_stages(self):
        wf = HCLWorkflow(_wfile('a', 'workflow'))
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

        wf = YMLWorkflow(_wfile('b', 'yml'))
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

    def test_substitutions(self):
        subs = [
            '_VAR1=sh', '_VAR2=ls', '_VAR4=test_env',
            '_VAR5=TESTING', '_VAR6=TESTER', '_VAR7=TEST'
        ]
        wf = YMLWorkflow(_wfile('substitutions', 'yml'))
        wf.parse(subs, False)
        self.assertDictEqual(wf.steps, {
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

        wf = YMLWorkflow(_wfile('substitutions', 'yml'))
        wf.parse(subs, False)
        self.assertDictEqual(wf.steps, {
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
        log.setLevel('CRITICAL')

    def tearDown(self):
        log.setLevel('NOTSET')

    def test_load_file(self):
        wf = HCLWorkflow("""workflow "sample" {
    resolves = "b"
}
action "a" {
    uses = "sh"
}
action "b" {
    needs = "a"
    uses = "sh"
}""")
        self.assertEqual(wf.wf_fmt, "hcl")
        self.assertDictEqual(
            wf.wf_dict, {
                'workflow': {
                    'sample': {
                        'resolves': 'b'}}, 'steps': {
                    'a': {
                        'uses': 'sh'}, 'b': {
                            'needs': 'a', 'uses': 'sh'}}})

    def test_normalize(self):
        wf = HCLWorkflow("""workflow "sample workflow" {
    resolves = "a"
}
action "a" {
    needs = "b"
    uses = "popperized/bin/npm@master"
    args = "npm --version"
    secrets = "SECRET_KEY"
}""")
        wf.normalize()
        self.assertEqual(wf.resolves, ['a'])
        self.assertEqual(wf.name, 'sample workflow')
        self.assertEqual(wf.on, 'push')
        self.assertDictEqual(wf.props, dict())
        step_a = wf.steps['a']
        self.assertEqual(step_a['name'], 'a')
        self.assertEqual(step_a['needs'], ['b'])
        self.assertEqual(step_a['args'], ['npm', '--version'])
        self.assertEqual(step_a['secrets'], ['SECRET_KEY'])

    def test_complete_graph(self):
        wf = HCLWorkflow(_wfile('a', 'workflow'))
        wf.normalize()
        wf.complete_graph()
        self.assertEqual(wf.name, 'example')
        self.assertEqual(wf.resolves, ['end'])
        self.assertEqual(wf.on, 'push')
        self.assertEqual(wf.props, {})
        self.assertEqual(wf.root, {'b', 'c', 'a'})

        steps_dict = {
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
        self.assertDictEqual(wf.steps, steps_dict)


class TestYMLWorkflow(unittest.TestCase):
    def setUp(self):
        log.setLevel('CRITICAL')

    def tearDown(self):
        log.setLevel('NOTSET')

    def test_load_file(self):
        wf = YMLWorkflow("""
        steps:
        - id: 'a'
          uses: 'sh'

        - id: 'b'
          uses: 'sh'
        """)
        self.assertEqual(wf.wf_fmt, "yml")
        self.assertDictEqual(
            wf.wf_dict, {
                'steps': {
                    'a': {
                        'uses': 'sh'}, 'b': {
                        'uses': 'sh'}}})
        self.assertListEqual(
            wf.wf_list,
            [{'uses': 'sh'}, {'uses': 'sh'}])
        self.assertDictEqual(
            wf.id_map,
            {1: 'a', 2: 'b'})

    def test_normalize(self):
        wf = YMLWorkflow("""
        steps:
        - id: "a"
          needs: "b"
          uses: "popperized/bin/npm@master"
          args: "npm --version"
          secrets: "SECRET_KEY"
        """)
        wf.normalize()
        self.assertEqual(wf.on, '')
        self.assertDictEqual(wf.props, dict())
        step_a = wf.steps['a']
        self.assertEqual(step_a['name'], 'a')
        self.assertEqual(step_a['needs'], ['b'])
        self.assertEqual(step_a['args'], ['npm', '--version'])
        self.assertEqual(step_a['secrets'], ['SECRET_KEY'])

    def test_get_containing_set(self):
        wf = YMLWorkflow(_wfile('a', 'yml'))
        wf.normalize()
        wf.complete_graph()
        set_1 = wf.get_containing_set(2)
        self.assertSetEqual(set_1, {'b', 'a', 'd'})

        wf = YMLWorkflow(_wfile('b', 'yml'))
        wf.normalize()
        wf.complete_graph()
        set_2 = wf.get_containing_set(3)
        self.assertSetEqual(set_2, {'c', 'b'})

    def test_complete_graph(self):
        wf = YMLWorkflow(_wfile('a', 'yml'))
        wf.normalize()
        wf.complete_graph()
        self.assertEqual(wf.name, 'a')
        self.assertEqual(wf.on, '')
        self.assertEqual(wf.props, {})
        self.assertEqual(wf.root, {'b', 'c', 'a'})

        steps_dict = {
            'a': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'a',
                'next': {'e'}
            },
            'b': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'b',
                'next': {'e'}
            },
            'c': {
                'uses': 'sh',
                'args': ['ls'],
                'name': 'c',
                'next': {'d'}
            }, 'd': {
                'needs': ['c'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'd',
                'next': {'e'}
            }, 'e': {
                'needs': ['d', 'b', 'a'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'e',
                'next': {'end'}
            }, 'end': {
                'needs': ['e'],
                'uses': 'sh',
                'args': ['ls'],
                'name': 'end'}
        }
        self.assertDictEqual(wf.steps, steps_dict)
