"""Handle's all the parsing and validation
functionality of `.workflow` files."""
from __future__ import unicode_literals
import os
from copy import deepcopy
from builtins import str, input, dict

import hcl

from popper.cli import log
from popper import utils as pu

# The valid Workflow and Action attributes.
VALID_ACTION_ATTRS = ["uses", "args", "needs", "runs", "secrets", "env"]
VALID_WORKFLOW_ATTRS = ["resolves", "on"]


class Workflow(object):
    """Represent's a immutable workflow.
    """

    def __init__(self, wfile):

        # Read's the workflow file.
        with open(wfile, 'r') as fp:
            self._workflow = hcl.load(fp)
            fp.seek(0)
            self._workflow_content = fp.readlines()

        self._validate_syntax()
        self._normalize()
        self._check_for_empty_workflow()
        self._complete_graph()

    @property
    def name(self):
        """The name of the workflow."""
        return self._workflow['name']

    @property
    def on(self):
        """The value of `on` attribute."""
        return self._workflow['on']

    @property
    def props(self):
        return self._workflow['props']

    @property
    def root(self):
        """The value of the `root` attribute."""
        return self._workflow['root']

    @property
    def resolves(self):
        """The value of the `resolves` attribute."""
        return self._workflow['resolves']

    @property
    def actions(self):
        """The list of actions in a workflow."""
        return self._workflow['action']

    def get_runner(self, action):
        """Returns the runner required to run an action."""
        return self._workflow['action'][action]['runner']

    def get_action(self, action):
        """Returns an action from a workflow."""
        return self._workflow['action'][action]

    @pu.threadsafe_generator
    def get_stages(self):
        """Generator of stages. A stages is a list of actions that can be
        executed in parallel.
        """
        current_stage = self._workflow['root']

        while current_stage:
            yield current_stage
            next_stage = set()
            for n in current_stage:
                next_stage.update(
                    self._workflow['action'][n].get(
                        'next', set()))
            current_stage = next_stage

    def _check_for_empty_workflow(self):
        actions = set(map(lambda a: a[0], self._workflow['action'].items()))
        if not set(self._workflow['resolves']).intersection(actions):
            log.fail('Can\'t resolve any of the actions.')

    def _complete_graph_util(self, entrypoint, nwd):
        """A GHA workflow is defined by specifying edges that point to the
        previous nodes they depend on. To make the workflow easier to process,
        we add forward edges. This also obtains the root nodes.

        Args:
            entrypoint (list): List of nodes from where to start
                               generating the graph.
            nwd (set) : Set of nodes without dependencies.
        """
        for node in entrypoint:
            if self._workflow['action'].get(node, None):
                if self._workflow['action'][node].get('needs', None):
                    for n in self._workflow['action'][node]['needs']:
                        self._complete_graph_util([n], nwd)
                        if not self._workflow['action'][n].get('next', None):
                            self._workflow['action'][n]['next'] = set()
                        self._workflow['action'][n]['next'].add(node)
                else:
                    nwd.add(node)
            else:
                log.fail('Action {} doesn\'t exist.'.format(node))

    def _complete_graph(self):
        """Driver function to run the recursive function
        `_complete_graph_util()` which adds forward edges.
        """
        nwd = set()
        self._complete_graph_util(self._workflow['resolves'], nwd)
        self._workflow['root'] = nwd

    @staticmethod
    def _is_list_of_strings(arr):
        """Utility function to check whether a list consists of only
        strings or not.

        Args:
            arr (list) : The list to verify.

        Returns:
            bool : Whether the list consists of only strings or not.
        """
        # Python 2 to 3 Compability
        try:
            basestring
        except UnboundLocalError:
            basestring = str
        return bool(arr) and isinstance(arr, list) and all(
            isinstance(elem, basestring) for elem in arr)

    def _validate_syntax(self):
        """ Validates the `.workflow` file by checking whether required items
        are specified, and if extra attributes not defined in the GHA
        specification are part of a workflow."""

        # Validates the workflow block
        if not self._workflow.get('workflow', None):
            log.fail('A workflow block must be present.')
        elif len(self._workflow['workflow'].items()) > 1:
            log.fail('Cannot have more than one workflow blocks.')
        else:
            wf_block = list(self._workflow['workflow'].values())[0]
            for key in wf_block.keys():
                if key not in VALID_WORKFLOW_ATTRS:
                    log.fail(
                        'Invalid workflow attribute \'{}\' was found.'.format(key))
            if not wf_block.get('resolves', None):
                log.fail('[resolves] attribute must be present.')

        # Validates the action blocks
        self._check_duplicate_actions()

        if not self._workflow.get('action', None):
            log.fail('Atleast one action block must be present.')
        else:
            for _, a_block in self._workflow['action'].items():
                for key in a_block.keys():
                    if key not in VALID_ACTION_ATTRS:
                        log.fail(
                            'Invalid action attribute \'{}\' was '
                            'found.'.format(key))
                if not a_block.get('uses', None):
                    log.fail('[uses] attribute must be present.')

    def _normalize(self):
        """Normalize the dictionary representation of the workflow by creating
        lists for all attributes that can be either a string or a list."""
        # move from this:
        #
        #  "workflow": {
        #    "test-and-deploy": {
        #      "resolves": "deploy"
        #    }
        #  }
        #
        # to this (top-level items in workflow dictionary):
        #
        #  "name": "test-and-deploy",
        #  "on": "push",
        #  "resolves": "deploy"
        #

        for wf_name, wf_block in dict(self._workflow['workflow']).items():
            self._workflow['name'] = wf_name
            self._workflow['on'] = wf_block.get('on', 'push')
            self._workflow['props'] = dict()
            self._workflow['resolves'] = wf_block['resolves']

        del(self._workflow['workflow'])

        # Python 2 to 3 Compability
        try:
            basestring
        except UnboundLocalError:
            basestring = str

        # Create a list for all attributes that can be either string or list
        if isinstance(self._workflow['resolves'], basestring):
            self._workflow['resolves'] = [self._workflow['resolves']]
        elif not self._is_list_of_strings(self._workflow['resolves']):
            log.fail('[resolves] must be a list of strings or a string')
        if not isinstance(self._workflow['on'], basestring):
            log.fail('[on] attribute must be a string')
        for a_name, a_block in self._workflow['action'].items():

            a_block['name'] = a_name

            if not isinstance(a_block['uses'], basestring):
                log.fail('[uses] attribute must be a string')
            if a_block.get('needs', None):
                if isinstance(a_block['needs'], basestring):
                    a_block['needs'] = [a_block['needs']]
                elif not self._is_list_of_strings(a_block['needs']):
                    log.fail(
                        '[needs] attribute must be a list of strings '
                        'or a string')
            if a_block.get('runs', None):
                if isinstance(a_block['runs'], basestring):
                    a_block['runs'] = [a_block['runs']]
                elif not self._is_list_of_strings(a_block['runs']):
                    log.fail(
                        '[runs] attribute must be a list of strings '
                        'or a string')
            if a_block.get('args', None):
                if isinstance(a_block['args'], basestring):
                    a_block['args'] = a_block['args'].split()
                elif not self._is_list_of_strings(a_block['args']):
                    log.fail(
                        '[args] attribute must be a list of strings '
                        'or a string')
            if a_block.get('env', None):
                if not isinstance(a_block['env'], dict):
                    log.fail('[env] attribute must be a dict')
            if a_block.get('secrets', None):
                if not self._is_list_of_strings(a_block['secrets']):
                    log.fail('[secrets] attribute must be a list of strings')

    def _check_duplicate_actions(self):
        """Checks whether duplicate action blocks are
        present or not."""
        parsed_acount = 0
        if self._workflow.get('action', None):
            parsed_acount = len(list(self._workflow['action'].items()))
        acount = 0
        for line in self._workflow_content:
            line = line.strip()
            if line.startswith('action '):
                acount += 1
        if parsed_acount != acount:
            log.fail('Duplicate action identifiers found.')

    def check_for_unreachable_actions(self, skip=None):
        """Validates a workflow by checking for unreachable nodes / gaps
        in the workflow.

        Args:
            workflow (Workflow) : The workflow object to validate.
        """
        def _traverse(entrypoint, visited, workflow):
            for node in entrypoint:
                visited.add(node)
                _traverse(workflow['action'][node].get(
                    'next', []), visited, workflow)

        visited = set()
        skipped = set(self._workflow['props'].get('skip_list', []))
        actions = set(map(lambda a: a[0], self._workflow['action'].items()))

        _traverse(self._workflow['root'], visited, self._workflow)

        unreachable = actions - visited - skipped
        if unreachable:
            if skip:
                log.fail('Actions {} are unreachable.'.format(
                    ', '.join(unreachable))
                )
            else:
                log.warn('Actions {} are unreachable.'.format(
                    ', '.join(unreachable))
                )

    def skip_actions(self, skip_list):
        """Removes the actions to be skipped from the workflow graph and
        return a new `Workflow` object.

        Args:
            workflow (Workflow) : The workflow object to operate upon.
            skip_list (list) : List of actions to be skipped.

        Returns:
            Workflow : The updated workflow object.
        """
        workflow = deepcopy(self)
        for sa_name in skip_list:
            try:
                sa_block = workflow.get_action(sa_name)
            except KeyError:
                log.fail('Action {} doesn\'t exist.'.format(sa_name))

            # Handle skipping of root action's
            if sa_name in workflow.root:
                workflow.root.remove(sa_name)

            # Handle skipping of not-root action's
            for a_name, a_block in workflow.actions.items():
                if sa_name in a_block.get('next', set()):
                    a_block['next'].remove(sa_name)
                    if a_name in sa_block.get('needs', []):
                        sa_block['needs'].remove(a_name)

        workflow.props['skip_list'] = list(skip_list)
        return workflow

    def filter_action(self, action, with_dependencies):
        """Filters out all actions except the one passed in
        the argument from the workflow.

        Args:
            action (str) : The action to run.

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
        workflow = deepcopy(self)
        actions = set(map(lambda x: x[0], workflow.actions.items()))

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
            workflow.actions.pop(a)

        return workflow
