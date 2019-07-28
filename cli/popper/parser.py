from __future__ import unicode_literals
from copy import deepcopy
from builtins import str, dict

import hcl

from popper.cli import log
from popper import utils as pu


VALID_ACTION_ATTRS = ["uses", "args", "needs", "runs", "secrets", "env"]
VALID_WORKFLOW_ATTRS = ["resolves", "on"]


class Workflow(object):
    """Represent's a immutable workflow.
    """

    def __init__(self, wfile):

        # Read and parse the workflow file.
        with open(wfile, 'r') as fp:
            self.parsed_workflow = hcl.load(fp)
            fp.seek(0)
            self.workflow_content = fp.readlines()

    def get_action(self, action):
        """Returns an action from a workflow."""
        if self.parsed_workflow['action'].get(action, None):
            return self.parsed_workflow['action'][action]
        else:
            log.fail("Action '{}' doesn\'t exist.".format(action))

    def parse(self):
        """Parse and validate a workflow."""
        self.validate_workflow_block()
        self.validate_action_blocks()
        self.normalize()
        self.check_for_empty_workflow()
        self.complete_graph()

    @pu.threadsafe_generator
    def get_stages(self):
        """Generator of stages. A stages is a list of actions that can be
        executed in parallel.
        """
        def resolve_intersections(stage):
            """Removes actions from a stage that creates
            conflict between the selected stage candidates."""
            actions_to_remove = set()
            for a in stage:
                if self.action[a].get('next', None):
                    intersection = self.action[a]['next'].intersection(stage)
                    if intersection:
                        for i in intersection:
                            actions_to_remove.add(i)

            for a in actions_to_remove:
                stage.remove(a)

        current_stage = self.root

        while current_stage:
            yield current_stage
            next_stage = set()
            for n in current_stage:
                next_stage.update(
                    self.action[n].get(
                        'next', set()))
                resolve_intersections(next_stage)
            current_stage = next_stage

    def check_for_empty_workflow(self):
        """Checks whether all the actions mentioned in resolves
        attribute is actually present in the workflow.

        If none of them are present, then the workflow is assumed to
        be empty and the execution halts.
        """
        actions_in_workflow = set(map(lambda a: a[0], self.action.items()))
        actions_in_resolves = set(self.resolves)
        if not actions_in_resolves.intersection(actions_in_workflow):
            log.fail(
                'Can\'t resolve any of the actions present in [resolves].')

    def find_root(self, entrypoint, root):
        """A GHA workflow is defined by specifying edges that point to the
        previous nodes they depend on. To make the workflow easier to process,
        we add forward edges. This also obtains the root nodes.

        Args:
            entrypoint (list): List of nodes from where to start
                               generating the graph.
            root (set) : Set of nodes without dependencies,
                         that would eventually be used as root.
        """
        for node in entrypoint:
            if self.get_action(node).get('needs', None):
                for n in self.action[node]['needs']:
                    self.find_root([n], root)
                    if not self.get_action(n).get('next', None):
                        self.action[n]['next'] = set()
                    self.action[n]['next'].add(node)
            else:
                root.add(node)

    def complete_graph(self):
        """Driver function to run the recursive function
        `_complete_graph_util()` which adds forward edges.
        """
        self.find_root(self.resolves, self.root)

    def validate_workflow_block(self):
        """Validate the syntax of the workflow block.
        """
        workflow_block_cnt = len(
            self.parsed_workflow.get(
                'workflow', dict()).items())
        if workflow_block_cnt == 0:
            log.fail('A workflow block must be present.')

        if workflow_block_cnt > 1:
            log.fail('Cannot have more than one workflow blocks.')

        workflow_block = list(self.parsed_workflow['workflow'].values())[0]
        for key in workflow_block.keys():
            if key not in VALID_WORKFLOW_ATTRS:
                log.fail(
                    'Invalid workflow attribute \'{}\' was found.'.format(key))

        if not workflow_block.get('resolves', None):
            log.fail('[resolves] attribute must be present in a '
                     'workflow block.')

        if not pu.of_type(workflow_block['resolves'], ['str', 'los']):
            log.fail('[resolves] attribute must be a string or a list '
                     'of strings.')

        if workflow_block.get('on', None):
            if not pu.of_type(workflow_block['on'], ['str']):
                log.fail('[on] attribute mist be a string.')

    def validate_action_blocks(self):
        """Validate the syntax of the action blocks.
        """
        self.check_duplicate_actions()
        if not self.parsed_workflow.get('action', None):
            log.fail('Atleast one action block must be present.')

        for _, a_block in self.parsed_workflow['action'].items():
            for key in a_block.keys():
                if key not in VALID_ACTION_ATTRS:
                    log.fail(
                        'Invalid action attribute \'{}\' found.'.format(key))

            if not a_block.get('uses', None):
                log.fail('[uses] attribute must be present in action block.')

            if not pu.of_type(a_block['uses'], ['str']):
                log.fail('[uses] attribute must be a string.')

            if a_block.get('needs', None):
                if not pu.of_type(a_block['needs'], ['str', 'los']):
                    log.fail(
                        '[needs] attribute must be a string or a list '
                        'of strings.')

            if a_block.get('args', None):
                if not pu.of_type(a_block['args'], ['str', 'los']):
                    log.fail(
                        '[args] attribute must be a string or a list '
                        'of strings.')

            if a_block.get('runs', None):
                if not pu.of_type(a_block['runs'], ['str', 'los']):
                    log.fail(
                        '[runs] attribute must be a string or a list '
                        'of strings.')

            if a_block.get('env', None):
                if not pu.of_type(a_block['env'], ['dict']):
                    log.fail('[env] attribute must be a dict.')

            if a_block.get('secrets', None):
                if not pu.of_type(a_block['secrets'], ['str', 'los']):
                    log.fail(
                        '[secrets] attribute must be a string or a list '
                        'of strings.')

    @staticmethod
    def format_command(params):
        """A static method that formats the `runs` and `args`
        attributes into a list of strings."""
        if isinstance(params, str):
            return params.split(" ")
        return params

    def normalize(self):
        """Takes properties from the `self.parsed_workflow` dict and
        makes them native to the `Workflow` class. Also it normalizes
        some of the attributes of a parsed workflow according to
        the Github defined specifications.

        For example, it changes `args`, `runs` and `secrets` attribute,
        if provided as a string to a list of string by splitting around
        whitespace. Also, it changes parameters like `uses` and `resolves`,
        if provided as a string to a list.
        """
        for wf_name, wf_block in self.parsed_workflow['workflow'].items():

            self.name = wf_name
            self.resolves = wf_block['resolves']
            self.on = wf_block.get('on', 'push')
            self.root = set()
            self.action = self.parsed_workflow['action']
            self.props = dict()

            if isinstance(self.resolves, str):
                self.resolves = [self.resolves]

        for a_name, a_block in self.action.items():
            a_block['name'] = a_name

            if a_block.get('needs', None):
                if isinstance(a_block['needs'], str):
                    a_block['needs'] = [a_block['needs']]

            if a_block.get('args', None):
                a_block['args'] = Workflow.format_command(a_block['args'])

            if a_block.get('runs', None):
                a_block['runs'] = Workflow.format_command(a_block['runs'])

            if a_block.get('secrets', None):
                a_block['secrets'] = Workflow.format_command(
                    a_block['secrets'])

    def check_duplicate_actions(self):
        """Checks whether duplicate action blocks are
        present or not."""
        parsed_acount = 0
        if self.parsed_workflow.get('action', None):
            parsed_acount = len(list(self.parsed_workflow['action'].items()))
        acount = 0
        for line in self.workflow_content:
            line = line.strip()
            if line.startswith('action '):
                acount += 1
        if parsed_acount != acount:
            log.fail('Duplicate action identifiers found.')

    def check_for_unreachable_actions(self, skip=None):
        """Validates a workflow by checking for unreachable nodes / gaps
        in the workflow.

        Args:
            skip (list) : The list actions to skip if applicable.
        """

        def _traverse(entrypoint, reachable, actions):
            for node in entrypoint:
                reachable.add(node)
                _traverse(actions[node].get(
                    'next', []), reachable, actions)

        reachable = set()
        skipped = set(self.props.get('skip_list', []))
        actions = set(map(lambda a: a[0], self.action.items()))

        _traverse(self.root, reachable, self.action)

        unreachable = actions - reachable
        if unreachable - skipped:
            if skip:
                log.fail('Actions {} are unreachable.'.format(
                    ', '.join(unreachable - skipped))
                )
            else:
                log.warning('Actions {} are unreachable.'.format(
                    ', '.join(unreachable))
                )

        for a in unreachable:
            self.action.pop(a)

    @staticmethod
    def skip_actions(wf, skip_list=list()):
        """Removes the actions to be skipped from the workflow graph and
        return a new `Workflow` object.

        Args:
            wf (Workflow) : The workflow object to operate upon.
            skip_list (list) : List of actions to be skipped.

        Returns:
            Workflow : The updated workflow object.
        """
        workflow = deepcopy(wf)
        for sa_name in skip_list:
            sa_block = workflow.get_action(sa_name)
            # Clear up all connections from sa_block
            sa_block.get('next', set()).clear()
            del sa_block.get('needs', list())[:]

            # Handle skipping of root action's
            if sa_name in workflow.root:
                workflow.root.remove(sa_name)

            # Handle skipping of non-root action's
            for a_name, a_block in workflow.action.items():
                if sa_name in a_block.get('next', set()):
                    a_block['next'].remove(sa_name)

                if sa_name in a_block.get('needs', list()):
                    a_block['needs'].remove(sa_name)

        workflow.props['skip_list'] = list(skip_list)
        return workflow

    @staticmethod
    def filter_action(wf, action, with_dependencies=False):
        """Filters out all actions except the one passed in
        the argument from the workflow.

        Args:
            wf (Workflow) : The workflow object to operate upon.
            action (str) : The action to run.
            with_dependencies (bool) : Filter out action to
            run with dependencies or not.

        Returns:
            Workflow : The updated workflow object.
        """
        # Recursively generate root when an action is run
        # with the `--with-dependencies` flag.
        def find_root_recursively(workflow, action, required_actions):
            required_actions.add(action)
            if workflow.get_action(action).get('needs', None):
                for a in workflow.get_action(action)['needs']:
                    find_root_recursively(workflow, a, required_actions)
                    if not workflow.get_action(a).get('next', None):
                        workflow.get_action(a)['next'] = set()
                    workflow.get_action(a)['next'].add(action)
            else:
                workflow.root.add(action)

        # The list of actions that needs to be preserved.
        workflow = deepcopy(wf)

        actions = set(map(lambda x: x[0], workflow.action.items()))

        required_actions = set()

        if with_dependencies:
            # Prepare the graph for running only the given action
            # only with its dependencies.
            find_root_recursively(workflow, action, required_actions)

            filtered_actions = actions - required_actions

            for ra in required_actions:
                a_block = workflow.get_action(ra)
                common_actions = filtered_actions.intersection(
                    a_block.get('next', set()))
                if common_actions:
                    for ca in common_actions:
                        a_block['next'].remove(ca)
        else:
            # Prepare the action for its execution only.
            required_actions.add(action)

            if workflow.get_action(action).get('next', None):
                workflow.get_action(action)['next'] = set()

            if workflow.get_action(action).get('needs', None):
                workflow.get_action(action)['needs'] = list()

            workflow.root.add(action)

        # Make the list of the actions to be removed.
        actions = actions - required_actions

        # Remove the remaining actions
        for a in actions:
            if a in workflow.root:
                workflow.root.remove(a)
            workflow.action.pop(a)

        return workflow
