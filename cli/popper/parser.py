from __future__ import unicode_literals
from copy import deepcopy
from builtins import str, dict

import hcl
import yaml

from popper.cli import log
from popper import utils as pu
import re
import os


VALID_ACTION_ATTRS = ["uses", "args", "needs", "runs", "secrets", "env"]
VALID_WORKFLOW_ATTRS = ["resolves", "on"]


class Workflow(object):
    """Represent's a immutable workflow."""

    def __init__(self, wfile, substitutions=None, allow_loose=False):
        self.wfile = wfile
        self.substitutions = substitutions
        self.allow_loose = allow_loose

    def parse(self):
        """Parse and validate a workflow.

        Args:
          substitutions(list): Substituitions that are to be passed
                                as an argumnets. (Default value = None)
          allow_loose(bool): Flag if the unused variables are to be
                                ignored. (Default value = False)

        Returns:
            None.

        """
        self.validate_workflow_block()
        self.validate_action_blocks()
        self.normalize()
        if self.substitutions:
            self.parse_substitutions(self.substitutions, self.allow_loose)
        self.check_for_broken_workflow()
        self.complete_graph()

    def load_file(self):
        raise NotImplementedError(
            "This method is required to be implemented in the derived class."
        )

    def complete_graph(self):
        raise NotImplementedError(
            "This method is required to be implemented in the derived class."
        )

    def normalize(self):
        raise NotImplementedError(
            "This method is required to be implemented in the derived class."
        )

    @staticmethod
    def format_command(params):
        """A static method that formats the `runs` and `args` attributes into a
        list of strings.

        Args:
          params(list/str): run or args that are being executed.

        Returns:
            list: List of strings of parameters.
        """
        if pu.of_type(params, ['str']):
            return params.split(" ")
        return params

    @pu.threadsafe_generator
    def get_stages(self):
        """Generator of stages. A stages is a list of actions that can be
        executed in parallel.

        Args:
            None

        Returns:
            None
        """
        def resolve_intersections(stage):
            """Removes actions from a stage that creates conflict between the
            selected stage candidates.

            Args:
              stage(set): Stage from which conflicted actions are to be
                            removed.

            Returns:
                None
            """
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

    def verify_action(self, action):
        return action in self.action.keys()

    def check_for_broken_workflow(self):
        action_dependencies = set()
        actions_in_workflow = set(self.action.keys())
        for a_name, a_block in self.action.items():
            action_dependencies.update(set(a_block.get('needs', list())))

        if self.wf_fmt == "hcl":
            action_dependencies.update(set(self.resolves))

        for action in action_dependencies:
            if not self.verify_action(action):
                log.fail(
                    'Action {} is referenced in the workflow '
                    'but is missing.'.format(action))

    def validate_workflow_block(self):
        """Validate the syntax of the workflow block.

        Args:
            None

        Returns:
            None
        """
        if self.wf_fmt == 'yml':
            return

        workflow_block_cnt = len(
            self.wf_dict.get(
                'workflow', dict()).items())
        if workflow_block_cnt == 0:
            log.fail('A workflow block must be present.')

        if workflow_block_cnt > 1:
            log.fail('Cannot have more than one workflow blocks.')

        workflow_block = list(self.wf_dict['workflow'].values())[0]
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

        Args:
            None

        Returns:
            None
        """
        self.check_duplicate_actions()

        if not self.wf_dict.get('action', None):
            log.fail('Atleast one action block must be present.')

        for _, a_block in self.wf_dict['action'].items():
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

    def check_duplicate_actions(self):
        """Checks whether duplicate action blocks are present or not.

        Args:
            None

        Returns:
            None
        """
        if self.wf_fmt == 'yml':
            action_line_identifier = '-'

        if self.wf_fmt == 'hcl':
            action_line_identifier = 'action '

        parsed_acount = 0
        if self.wf_dict.get('action', None):
            parsed_acount = len(list(self.wf_dict['action'].items()))
        acount = 0
        for line in self.wf_content:
            line = line.strip()
            if line.startswith(action_line_identifier):
                acount += 1
        if parsed_acount != acount:
            log.fail('Duplicate action identifiers found.')

    def check_for_unreachable_actions(self, skip=None):
        """Validates a workflow by checking for unreachable nodes / gaps in the
        workflow.

        Args:
          skip(list, optional): The list actions to skip if applicable.
                                (Default value = None)

        Returns:
            None
        """

        def _traverse(entrypoint, reachable, actions):
            """

            Args:
              entrypoint(set): Set containing the entry point of part of the
                                workflow.
              reachable(set): Set containing all the reachable parts of
                                workflow.
              actions(dict): Dictionary containing the identifier of the
                                workflow and its description.

            Returns:
                None
            """
            for node in entrypoint:
                reachable.add(node)
                _traverse(actions[node].get(
                    'next', []), reachable, actions)

        if self.wf_fmt == 'yml':
            return

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

    def parse_substitutions(self, substitutions, allow_loose):
        """

        Args:
          substitutions(list): List of substitutions that are passed
                                as an arguments.
          allow_loose(bool): Flag used to ignore unused substitution
                                variable in the workflow.

        Returns:
            None

        """

        substitution_dict = dict()

        for args in substitutions:
            item = args.split('=', 1)
            if len(item) < 2:
                raise Exception("Excepting '=' as seperator")
            substitution_dict['$' + item[0]] = item[1]

        for keys in substitution_dict:
            if(not bool(re.match(r"\$_[A-Z0-9]+", keys))):
                log.fail("Substitution variable '{}' doesn't "
                         "satify required format ".format(keys))

        used = {}

        for wf_name, wf_block in self.action.items():

            attr = wf_block.get('needs', [])
            for i in range(len(attr)):
                for k, v in substitution_dict.items():
                    if k in attr[i]:
                        used[k] = 1
                        attr[i] = attr[i].replace(k, v)

            attr = wf_block.get('uses', '')
            for k, v in substitution_dict.items():
                if k in attr:
                    used[k] = 1
                    wf_block['uses'] = attr.replace(k, v)

            attr = wf_block.get('args', [])
            for i in range(len(attr)):
                for k, v in substitution_dict.items():
                    if k in attr[i]:
                        used[k] = 1
                        attr[i] = attr[i].replace(k, v)

            attr = wf_block.get('runs', [])
            for i in range(len(attr)):
                for k, v in substitution_dict.items():
                    if k in attr[i]:
                        used[k] = 1
                        attr[i] = attr[i].replace(k, v)

            attr = wf_block.get('secrets', [])
            for i in range(len(attr)):
                for k, v in substitution_dict.items():
                    if k in attr[i]:
                        used[k] = 1
                        attr[i] = attr[i].replace(k, v)

            attr = wf_block.get('env', {})
            temp_dict = {}
            for key in attr.keys():
                check_replacement = False
                for k, v in substitution_dict.items():
                    if k in key:
                        used[k] = 1
                        temp_dict[v] = attr[key]
                        check_replacement = True

                if(check_replacement is False):
                    temp_dict[key] = attr[key]

            for key, value in temp_dict.items():
                for k, v in substitution_dict.items():
                    if k in value:
                        used[k] = 1
                        temp_dict[key] = v

            if(len(temp_dict) != 0):
                wf_block['env'] = temp_dict

        if not allow_loose and len(substitution_dict) != len(used):
            log.fail("Not all given substitutions are used in"
                     "the workflow file")

    @staticmethod
    def skip_actions(wf, skip_list=list()):
        """Removes the actions to be skipped from the workflow graph and return
        a new `Workflow` object.

        Args:
          wf(Workflow): The workflow object to operate upon.
          skip_list(list): List of actions to be skipped.
                            (Default value = list())

        Returns:
          Workflow : The updated workflow object.
        """
        workflow = deepcopy(wf)
        for sa_name in skip_list:
            if not workflow.verify_action(sa_name):
                log.fail(
                    'Action {} can\'t be skipped as it is '
                    'missing from the workflow.'.format(sa_name))
            sa_block = workflow.action[sa_name]
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
        """Filters out all actions except the one passed in the argument from
        the workflow.
        Args:
          wf(Workflow): The workflow object to operate upon.
          action(str): The action to run.
          with_dependencies(bool, optional): Filter out action to
        run with dependencies or not. (Default value = False)
        Returns:
          Workflow: The updated workflow object.
        """
        # Recursively generate root when an action is run
        # with the `--with-dependencies` flag.
        def find_root_recursively(workflow, action, required_actions):
            """
            Args:
              workflow(worklfow): The workflow object to operate upon.
              action(str): The action to run.
              required_actions(set): Set containing actions that are
                                    to be executed.
            Returns:
                None
            """
            required_actions.add(action)
            if workflow.action[action].get('needs', None):
                for a in workflow.action[action]['needs']:
                    find_root_recursively(workflow, a, required_actions)
                    if not workflow.action[a].get('next', None):
                        workflow.action[a]['next'] = set()
                    workflow.action[a]['next'].add(action)
            else:
                workflow.root.add(action)

        # The list of actions that needs to be preserved.
        workflow = deepcopy(wf)

        if not workflow.verify_action(action):
            log.fail(
                'Action {} can\'t be filtered as it is '
                'missing from the workflow.'.format(action))

        actions = set(map(lambda x: x[0], workflow.action.items()))

        required_actions = set()

        if with_dependencies:
            # Prepare the graph for running only the given action
            # only with its dependencies.
            find_root_recursively(workflow, action, required_actions)

            filtered_actions = actions - required_actions

            for ra in required_actions:
                a_block = workflow.action[ra]
                common_actions = filtered_actions.intersection(
                    a_block.get('next', set()))
                if common_actions:
                    for ca in common_actions:
                        a_block['next'].remove(ca)
        else:
            # Prepare the action for its execution only.
            required_actions.add(action)

            if workflow.action[action].get('next', None):
                workflow.action[action]['next'] = set()

            if workflow.action[action].get('needs', None):
                workflow.action[action]['needs'] = list()

            workflow.root.add(action)

        # Make the list of the actions to be removed.
        actions = actions - required_actions

        # Remove the remaining actions
        for a in actions:
            if a in workflow.root:
                workflow.root.remove(a)
            workflow.action.pop(a)

        return workflow


class YMLWorkflow(Workflow):
    """Parse a yml based workflow and generate the workflow graph.
    """

    def __init__(self, wfile, substitutions=None, allow_loose=False):
        super(YMLWorkflow, self).__init__(wfile, substitutions, allow_loose)
        self.wf_fmt = "yml"
        self.load_file()

    def load_file(self):
        """Loads the workflow as a dict from the `.yml` file.

        Args:
            None

        Returns:
            None
        """
        with open(self.wfile) as fp:
            self.wf_list = yaml.safe_load(fp)['steps']
            fp.seek(0)
            self.wf_content = fp.readlines()
            if not self.wf_list:
                return

        self.wf_dict = {'action': dict()}
        self.id_map = dict()

        for idx, action in enumerate(self.wf_list):
            # If no id attribute present, make one
            _id = action.get('id', str(idx + 1))
            self.wf_dict['action'][_id] = action
            self.id_map[idx + 1] = _id
            action.pop('id', None)

    def normalize(self):
        """Takes properties from the `self.wf_dict` dict and makes them
        native to the `Workflow` class. Also it normalizes some of the
        attributes of a parsed workflow according to the Github defined
        specifications.

        For example, it changes `args`, `runs` and `secrets` attribute,
        if provided as a string to a list of string by splitting around
        whitespace. Also, it changes parameters like `uses` and `resolves`,
        if provided as a string to a list.

        Args:
            None

        Returns:
            None
        """
        self.name = os.path.basename(self.wfile)[:-4]
        self.on = ""
        self.root = set()
        self.props = dict()
        self.action = self.wf_dict['action']

        for a_name, a_block in self.action.items():
            a_block['name'] = a_name

            if a_block.get('needs', None):
                if pu.of_type(a_block['needs'], ['str']):
                    a_block['needs'] = [a_block['needs']]

            if a_block.get('args', None):
                a_block['args'] = Workflow.format_command(a_block['args'])

            if a_block.get('runs', None):
                a_block['runs'] = Workflow.format_command(a_block['runs'])

            if a_block.get('secrets', None):
                a_block['secrets'] = Workflow.format_command(
                    a_block['secrets'])

    def get_containing_stage(self, idx):
        """Find the stage from the list of stages, where
        the action with the given index is present.

        Args:
            idx(int): The index of the action to be searched.

        Returns:
            set: The required stage.
        """
        for stage in self.stages:
            if self.id_map[idx] in stage:
                return stage

        required_stage = set()
        required_stage.add(self.id_map[idx])
        return required_stage

    def complete_graph(self):
        """Function to generate the workflow graph by
        adding forward edges.

        Args:
            None

        Returns:
            None
        """
        # Connect the graph as much as possible.
        for a_id, a_block in self.action.items():
            if a_block.get('needs', None):
                for a in a_block['needs']:
                    if not self.action[a].get('next', None):
                        self.action[a]['next'] = set()
                    self.action[a]['next'].add(a_id)

        # Generate the potential stages.
        self.stages = list()
        self.visited = dict()

        for a_id, a_block in self.action.items():
            if a_block.get('next', None):
                if a_block['next'] not in self.stages:
                    self.stages.append(a_block['next'])
                    self.visited[tuple(a_block['next'])] = False

            if a_block.get('needs', None):
                if a_block['needs'] not in self.stages:
                    self.stages.append(set(a_block['needs']))
                    self.visited[tuple(a_block['needs'])] = False

        # Moving from top to bottom
        for idx, id in self.id_map.items():
            action = self.action[id]
            if not action.get('next', None):
                # if this is not the last action,
                if idx + 1 <= len(self.action.items()):
                    curr = self.id_map[idx]
                    next = self.id_map[idx + 1]
                    # If the current action and next action is not in any
                    # stage,
                    if ({curr, next} not in self.stages) and (
                            {next, curr} not in self.stages):
                        next_stage = self.get_containing_stage(idx + 1)
                        curr_stage = self.get_containing_stage(idx)

                        if not self.visited.get(tuple(next_stage), None):
                            action['next'] = next_stage
                            for nsa in next_stage:
                                self.action[nsa]['needs'] = id
                            self.visited[tuple(curr_stage)] = True

        # Finally, generate the root.
        for a_id, a_block in self.action.items():
            if not a_block.get('needs', None):
                self.root.add(a_id)


class HCLWorkflow(Workflow):
    """Parse a hcl based workflow and generate
    the workflow graph.
    """

    def __init__(self, wfile, substitutions=None, allow_loose=False):
        super(HCLWorkflow, self).__init__(wfile, substitutions, allow_loose)
        self.wf_fmt = "hcl"
        self.load_file()

    def load_file(self):
        """Loads the workflow as a dict from the `.workflow` file.

        Args:
            None

        Returns:
            None
        """
        with open(self.wfile) as fp:
            self.wf_dict = hcl.load(fp)
            fp.seek(0)
            self.wf_content = fp.readlines()

    def find_root(self, entrypoint, root):
        """A GHA workflow is defined by specifying edges that point to the
        previous nodes they depend on. To make the workflow easier to process,
        we add forward edges. This also obtains the root nodes.

        Args:
          entrypoint(list): List of nodes from where to start
        generating the graph.
          root(set): Set of nodes without dependencies,
        that would eventually be used as root.

        Returns:
            None
        """
        for node in entrypoint:
            if self.action[node].get('needs', None):
                for n in self.action[node]['needs']:
                    self.find_root([n], root)
                    if not self.action[n].get('next', None):
                        self.action[n]['next'] = set()
                    self.action[n]['next'].add(node)
            else:
                root.add(node)

    def complete_graph(self):
        """Driver function to run the recursive function
        `find_root()` which adds forward edges.

        Args:
            None

        Returns:
            None
        """
        self.find_root(self.resolves, self.root)

    def normalize(self):
        """Takes properties from the `self.wf_dict` dict and makes them
        native to the `Workflow` class. Also it normalizes some of the
        attributes of a parsed workflow according to the Github defined
        specifications.

        For example, it changes `args`, `runs` and `secrets` attribute,
        if provided as a string to a list of string by splitting around
        whitespace. Also, it changes parameters like `uses` and `resolves`,
        if provided as a string to a list.

        Args:
            None

        Returns:
            None
        """
        for wf_name, wf_block in self.wf_dict['workflow'].items():

            self.name = wf_name
            self.resolves = wf_block['resolves']
            self.on = wf_block.get('on', 'push')
            self.root = set()
            self.action = self.wf_dict['action']
            self.props = dict()

            if pu.of_type(self.resolves, ['str']):
                self.resolves = [self.resolves]

        for a_name, a_block in self.action.items():
            a_block['name'] = a_name

            if a_block.get('needs', None):
                if pu.of_type(a_block['needs'], ['str']):
                    a_block['needs'] = [a_block['needs']]

            if a_block.get('args', None):
                a_block['args'] = Workflow.format_command(a_block['args'])

            if a_block.get('runs', None):
                a_block['runs'] = Workflow.format_command(a_block['runs'])

            if a_block.get('secrets', None):
                a_block['secrets'] = Workflow.format_command(
                    a_block['secrets'])
