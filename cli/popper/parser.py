"""Handle's all the parsing and validation
functionality of `.workflow` files."""
from __future__ import unicode_literals
import os
from builtins import str, input, dict

import hcl

from popper.cli import log
from popper import utils as pu

# The valid Workflow and Action attributes.
VALID_ACTION_ATTRS = ["uses", "args", "needs", "runs", "secrets", "env"]
VALID_WORKFLOW_ATTRS = ["resolves", "on"]


class Workflow(object):
    """Represent's a workflow.
    """

    def __init__(self, workflow_file):

        # Read's the workflow file.
        with open(workflow_file, 'r') as fp:
            self.workflow = hcl.load(fp)
            fp.seek(0)
            self.workflow_content = fp.readlines()

        self.validate_syntax()
        self.normalize()
        self.complete_graph()

    @property
    def name(self):
        """The name of the workflow."""
        return self.workflow['name']

    @property
    def on(self):
        """The value of `on` attribute."""
        return self.workflow['on']

    @property
    def root(self):
        """The value of the `root` attribute."""
        return self.workflow['root']

    @property
    def resolves(self):
        """The value of the `resolves` attribute."""
        return self.workflow['resolves']

    @property
    def actions(self):
        """The list of actions in a workflow."""
        return self.workflow['action'].items()

    def get_runner(self, action):
        """Returns the runner required to run an action."""
        return self.workflow['action'][action]['runner']

    def get_action(self, action):
        """Returns an action from a workflow."""
        return self.workflow['action'][action]

    @pu.threadsafe_generator
    def get_stages(self):
        """Generator of stages. A stages is a list of actions that can be
        executed in parallel.
        """
        current_stage = self.workflow['root']

        while current_stage:
            yield current_stage
            next_stage = set()
            for n in current_stage:
                next_stage.update(
                    self.workflow['action'][n].get(
                        'next', set()))
            current_stage = next_stage

    def complete_graph(self):
        """A GHA workflow is defined by specifying edges that point to the
        previous nodes they depend on. To make the workflow easier to process,
        we add forward edges. This also obtains the root nodes.
        """
        nodes_without_dependencies = set()
        root_nodes = set()

        for name, a_block in self.workflow['action'].items():

            a_block['name'] = name

            for n in a_block.get('needs', []):
                if not self.workflow['action'][n].get('next', None):
                    self.workflow['action'][n]['next'] = set()
                self.workflow['action'][n]['next'].add(name)

            if not a_block.get('needs', None):
                nodes_without_dependencies.add(name)

        # a root node is:
        # - reachable from the workflow's 'resolves' node
        # - a node without dependencies
        for n in set(nodes_without_dependencies):
            if (self.workflow['action'][n].get('next', None)
                    or n in self.workflow['resolves']):
                nodes_without_dependencies.remove(n)
                root_nodes.add(n)

        if nodes_without_dependencies:
            log.warn(
                "These actions are unreachable and won't be "
                "executed: {}".format(','.join(nodes_without_dependencies)))

        self.workflow['root'] = list(root_nodes)

    @staticmethod
    def is_list_of_strings(arr):
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

    def validate_syntax(self):
        """ Validates the `.workflow` file by checking whether required items
        are specified, and if extra attributes not defined in the GHA
        specification are part of a workflow."""

        # Validates the workflow block
        if not self.workflow.get('workflow', None):
            log.fail('A workflow block must be present.')
        elif len(self.workflow['workflow'].items()) > 1:
            log.fail('Cannot have more than one workflow blocks.')
        else:
            wf_block = list(self.workflow['workflow'].values())[0]
            for key in wf_block.keys():
                if key not in VALID_WORKFLOW_ATTRS:
                    log.fail('Invalid attrs found.')
            if not wf_block.get('resolves', None):
                log.fail('[resolves] attribute must be present.')

        # Validates the action blocks
        self.check_duplicate_actions()

        if not self.workflow.get('action', None):
            log.fail('Atleast one action block must be present.')
        else:
            for _, a_block in self.workflow['action'].items():
                for key in a_block.keys():
                    if key not in VALID_ACTION_ATTRS:
                        log.fail('Invalid attrs found.')
                if not a_block.get('uses', None):
                    log.fail('[uses] attribute must be present.')

    def normalize(self):
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

        for wf_name, wf_block in dict(self.workflow['workflow']).items():
            self.workflow['name'] = wf_name
            self.workflow['on'] = wf_block.get('on', 'push')
            self.workflow['resolves'] = wf_block['resolves']

        del(self.workflow['workflow'])

        # Python 2 to 3 Compability
        try:
            basestring
        except UnboundLocalError:
            basestring = str

        # Create a list for all attributes that can be either string or list
        if isinstance(self.workflow['resolves'], basestring):
            self.workflow['resolves'] = [self.workflow['resolves']]
        elif not self.is_list_of_strings(self.workflow['resolves']):
            log.fail('[resolves] must be a list of strings or a string')
        if not isinstance(self.workflow['on'], basestring):
            log.fail('[on] attribute must be a string')
        for _, a_block in self.workflow['action'].items():
            if not isinstance(a_block['uses'], basestring):
                log.fail('[uses] attribute must be a string')
            if a_block.get('needs', None):
                if isinstance(a_block['needs'], basestring):
                    a_block['needs'] = [a_block['needs']]
                elif not self.is_list_of_strings(a_block['needs']):
                    log.fail(
                        '[needs] attribute must be a list of strings '
                        'or a string')
            if a_block.get('runs', None):
                if isinstance(a_block['runs'], basestring):
                    a_block['runs'] = [a_block['runs']]
                elif not self.is_list_of_strings(a_block['runs']):
                    log.fail(
                        '[runs] attribute must be a list of strings '
                        'or a string')
            if a_block.get('args', None):
                if isinstance(a_block['args'], basestring):
                    a_block['args'] = a_block['args'].split()
                elif not self.is_list_of_strings(a_block['args']):
                    log.fail(
                        '[args] attribute must be a list of strings '
                        'or a string')
            if a_block.get('env', None):
                if not isinstance(a_block['env'], dict):
                    log.fail('[env] attribute must be a dict')
            if a_block.get('secrets', None):
                if not self.is_list_of_strings(a_block['secrets']):
                    log.fail('[secrets] attribute must be a list of strings')

    def check_duplicate_actions(self):
        """Checks whether duplicate action blocks are
        present or not."""
        parsed_acount = 0
        if self.workflow.get('action', None):
            parsed_acount = len(list(self.workflow['action'].items()))
        acount = 0
        for line in self.workflow_content:
            line = line.strip()
            if line.startswith('action '):
                acount += 1
        if parsed_acount != acount:
            log.fail('Duplicate action identifiers found.')
