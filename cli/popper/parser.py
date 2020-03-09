from __future__ import unicode_literals

import re
import hcl
import os
import yaml

from copy import deepcopy
from builtins import str, dict
from popper.cli import log as log

import popper.utils as pu


VALID_STEP_ATTRS = ["uses", "args", "needs", "runs", "secrets", "env", "name", "next"]


class Workflow(object):
    """Represents an immutable workflow."""

    def __init__(self):
        pass

    def parse(self, substitutions=None, allow_loose=False):
        """Parse and validate a workflow.

        Args:
          substitutions(list): Substitutions that are to be passed
                                as an arguments. (Default value = None)
          allow_loose(bool): Flag if the unused variables are to be
                                ignored. (Default value = False)

        Returns:
            None.

        """
        self.validate_workflow_block()
        self.validate_step_blocks()
        self.normalize()
        self.parse_substitutions(substitutions, allow_loose)
        self.check_for_broken_workflow()
        self.complete_graph()

    def complete_graph(self):
        raise NotImplementedError(
            "This method is required to be implemented in the derived class."
        )

    def normalize(self):
        raise NotImplementedError(
            "This method is required to be implemented in the derived class."
        )

    @staticmethod
    def new(file, step=None, skipped_steps=[], substitutions=[],
            allow_loose=False, include_step_dependencies=False):
        if file.endswith('.workflow'):
            wf = HCLWorkflow(file)
        elif file.endswith('.yml') or file.endswith('.yaml'):
            wf = YMLWorkflow(file)
        else:
            log.fail('Unrecognized workflow file format.')

        wf.parse(substitutions=substitutions, allow_loose=allow_loose)

        log.debug(
            f'Parsed workflow:\n'
            f'{yaml.dump(wf, default_flow_style=False, default_style="")}')

        wf = Workflow.skip_steps(wf, skipped_steps)
        wf = Workflow.filter_step(wf, step, include_step_dependencies)

        wf.check_for_unreachable_steps(skipped_steps)

        return wf

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
        """Generator of stages. A stages is a list of steps that can be
        executed in parallel.
        """
        def resolve_intersections(stage):
            """Removes steps from a stage that creates conflict between the
            selected stage candidates.

            Args:
              stage(set): Stage from which conflicted steps are to be
                            removed.

            Returns:
                None
            """
            steps_to_remove = set()
            for a in stage:
                if self.steps[a].get('next', None):
                    intersection = self.steps[a]['next'].intersection(stage)
                    if intersection:
                        for i in intersection:
                            steps_to_remove.add(i)

            for a in steps_to_remove:
                stage.remove(a)

        current_stage = self.root

        while current_stage:
            yield current_stage
            next_stage = set()
            for n in current_stage:
                next_stage.update(self.steps[n].get('next', set()))
                resolve_intersections(next_stage)
            current_stage = next_stage

    def check_for_broken_workflow(self):
        step_dependencies = set()
        for a_name, a_block in self.steps.items():
            step_dependencies.update(set(a_block.get('needs', list())))

        if self.wf_fmt == "hcl":
            step_dependencies.update(set(self.resolves))

        for step in step_dependencies:
            if step not in self.steps:
                log.fail(f"Step '{step}' referenced in workflow but missing")

    def validate_workflow_block(self):
        """Validate the syntax of the workflow block."""
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
                log.fail(f"Invalid workflow attribute '{key}'.")

        if not workflow_block.get('resolves', None):
            log.fail('[resolves] attribute must be present in a '
                     'workflow block.')

        if not pu.of_type(workflow_block['resolves'], ['str', 'los']):
            log.fail('[resolves] attribute must be a string or a list '
                     'of strings.')

        if workflow_block.get('on', None):
            if not pu.of_type(workflow_block['on'], ['str']):
                log.fail('[on] attribute mist be a string.')

    def validate_step_blocks(self):
        """Validate the syntax of the step blocks."""
        if not self.wf_dict.get('steps', None):
            log.fail('At least one step block must be present.')

        for _, a_block in self.wf_dict['steps'].items():
            for key in a_block.keys():
                if key not in VALID_STEP_ATTRS:
                    log.fail(f"Invalid step attribute '{key}'.")

            if not a_block.get('uses', None):
                log.fail('[uses] attribute must be present in step block.')

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

    def check_for_unreachable_steps(self, skip=None):
        """Validates a workflow by checking for unreachable nodes / gaps in the
        workflow.

        Args:
          skip(list, optional): The list of steps to skip if applicable.
                                (Default value = None)

        Returns:
            None
        """
        if not skip or self.wf_fmt == 'yml':
            # noop
            return

        def _traverse(entrypoint, reachable, steps):
            """

            Args:
              entrypoint(set): Set containing the entry point of part of the
                                workflow.
              reachable(set): Set containing all the reachable parts of
                                workflow.
              steps(dict): Dictionary containing the identifier of the
                                workflow and its description.

            Returns:
                None
            """
            for node in entrypoint:
                reachable.add(node)
                _traverse(steps[node].get(
                    'next', []), reachable, steps)

        reachable = set()
        skipped = set(self.props.get('skip_list', []))
        steps = set(map(lambda a: a[0], self.steps.items()))

        _traverse(self.root, reachable, self.steps)

        unreachable = steps - reachable
        if unreachable - skipped:
            if skip:
                log.fail(
                    f'Unreachable step(s): {", ".join(unreachable-skipped)}.')
            else:
                log.warning(f'Unreachable step(s): {", ".join(unreachable)}.')

        for a in unreachable:
            self.steps.pop(a)

    def parse_substitutions(self, substitutions=None, allow_loose=False):
        """

        Args:
          substitutions(list): List of substitutions that are passed
                                as an arguments.
          allow_loose(bool): Flag used to ignore unused substitution
                                variable in the workflow.

        Returns:
            None

        """

        if not substitutions:
            # noop
            return

        substitution_dict = dict()

        for args in substitutions:
            item = args.split('=', 1)
            if len(item) < 2:
                raise Exception("Excepting '=' as seperator")
            substitution_dict['$' + item[0]] = item[1]

        for keys in substitution_dict:
            if not re.match(r"\$_[A-Z0-9]+", keys):
                log.fail(f"Improper substitution format: '{keys}'.")

        used = {}

        for wf_name, wf_block in self.steps.items():

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
    def skip_steps(wf, skip_list=[]):
        """Removes the steps to be skipped from the workflow graph and return
        a new `Workflow` object.

        Args:
          wf(Workflow): The workflow object to operate upon.
          skip_list(list): List of steps to be skipped.
                            (Default value = list())

        Returns:
          Workflow : The updated workflow object.
        """
        if not skip_list:
            # noop
            return wf

        workflow = deepcopy(wf)
        for sa_name in skip_list:
            if sa_name not in workflow.steps:
                log.fail(f"Referenced step '{sa_name} missing.")
            sa_block = workflow.steps[sa_name]
            # Clear up all connections from sa_block
            sa_block.get('next', set()).clear()
            del sa_block.get('needs', list())[:]

            # Handle skipping of root step's
            if sa_name in workflow.root:
                workflow.root.remove(sa_name)

            # Handle skipping of non-root step's
            for a_name, a_block in workflow.steps.items():
                if sa_name in a_block.get('next', set()):
                    a_block['next'].remove(sa_name)

                if sa_name in a_block.get('needs', list()):
                    a_block['needs'].remove(sa_name)

        workflow.props['skip_list'] = list(skip_list)
        return workflow

    @staticmethod
    def filter_step(wf, step, with_dependencies=False):
        """Filters out all steps except the one passed in the argument from
        the workflow.
        Args:
          wf(Workflow): The workflow object to operate upon.
          step(str): The step to run.
          with_dependencies(bool, optional): Filter out step to
        run with dependencies or not. (Default value = False)
        Returns:
          Workflow: The updated workflow object.
        """

        if not step:
            # noop
            return wf

        # Recursively generate root when an step is run
        # with the `--with-dependencies` flag.
        def find_root_recursively(workflow, step, required_steps):
            """
            Args:
              workflow(worklfow): The workflow object to operate upon.
              step(str): The step to run.
              required_steps(set): Set containing steps that are
                                    to be executed.
            Returns:
                None
            """
            required_steps.add(step)
            if workflow.steps[step].get('needs', None):
                for a in workflow.steps[step]['needs']:
                    find_root_recursively(workflow, a, required_steps)
                    if not workflow.steps[a].get('next', None):
                        workflow.steps[a]['next'] = set()
                    workflow.steps[a]['next'].add(step)
            else:
                workflow.root.add(step)

        # The list of steps that needs to be preserved.
        workflow = deepcopy(wf)

        if step not in workflow.steps:
            log.fail(f"Referenced step '{step}' missing.")

        steps = set(map(lambda x: x[0], workflow.steps.items()))

        required_steps = set()

        if with_dependencies:
            # Prepare the graph for running only the given step
            # only with its dependencies.
            find_root_recursively(workflow, step, required_steps)

            filtered_steps = steps - required_steps

            for ra in required_steps:
                a_block = workflow.steps[ra]
                common_steps = filtered_steps.intersection(
                    a_block.get('next', set()))
                if common_steps:
                    for ca in common_steps:
                        a_block['next'].remove(ca)
        else:
            # Prepare the step for its execution only.
            required_steps.add(step)

            if workflow.steps[step].get('next', None):
                workflow.steps[step]['next'] = set()

            if workflow.steps[step].get('needs', None):
                workflow.steps[step]['needs'] = list()

            workflow.root.add(step)

        # Make the list of the steps to be removed.
        steps = steps - required_steps

        # Remove the remaining steps
        for a in steps:
            if a in workflow.root:
                workflow.root.remove(a)
            workflow.steps.pop(a)

        return workflow


class YMLWorkflow(Workflow):
    """Parse a yml based workflow and generate the workflow graph.
    """

    def __init__(self, wfile):
        """Loads the workflow as a dict from the `.yml` file."""
        super(YMLWorkflow, self).__init__()
        self.wf_fmt = "yml"

        if not os.path.exists(wfile):
            # try to load string
            self.wf_list = yaml.safe_load(wfile)['steps']
        else:
            with open(wfile) as fp:
                self.wf_list = yaml.safe_load(fp)['steps']
                if not self.wf_list:
                    return

        self.wf_dict = {'steps': dict()}
        self.id_map = dict()

        for idx, step in enumerate(self.wf_list):
            # If no id attribute present, make one
            _id = str(step.get('id', idx + 1))
            self.wf_dict['steps'][_id] = step
            self.id_map[idx + 1] = _id
            step.pop('id', None)

        self.name = os.path.basename(wfile)[:-4]

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
        self.on = ""
        self.root = set()
        self.props = dict()
        self.steps = self.wf_dict['steps']

        for a_name, a_block in self.steps.items():
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

    def get_containing_set(self, idx):
        """Find the set from the list of sets of step dependencies, where
        the step with the given index is present.

        Args:
            idx(int): The index of the step to be searched.

        Returns:
            set: The required set.
        """
        for _set in self.dep_sets:
            if self.id_map[idx] in _set:
                return _set

        required_set = set()
        required_set.add(self.id_map[idx])
        return required_set

    def complete_graph(self):
        """Function to generate the workflow graph by adding forward edges.

        Args:
            None

        Returns:
            None
        """
        # Connect the graph as much as possible.
        for a_id, a_block in self.steps.items():
            if a_block.get('needs', None):
                for a in a_block['needs']:
                    if not self.steps[a].get('next', None):
                        self.steps[a]['next'] = set()
                    self.steps[a]['next'].add(a_id)

        # Generate the dependency sets.
        self.dep_sets = list()
        self.visited = dict()

        for a_id, a_block in self.steps.items():
            if a_block.get('next', None):
                if a_block['next'] not in self.dep_sets:
                    self.dep_sets.append(a_block['next'])
                    self.visited[tuple(a_block['next'])] = False

            if a_block.get('needs', None):
                if a_block['needs'] not in self.dep_sets:
                    self.dep_sets.append(set(a_block['needs']))
                    self.visited[tuple(a_block['needs'])] = False

        # Moving from top to bottom
        for idx, id in self.id_map.items():
            step = self.steps[id]
            if not step.get('next', None):
                # if this is not the last step,
                if idx + 1 <= len(self.steps):
                    curr = self.id_map[idx]
                    next = self.id_map[idx + 1]
                    # If the current step and next step is not in any
                    # set,
                    if ({curr, next} not in self.dep_sets) and (
                            {next, curr} not in self.dep_sets):
                        next_set = self.get_containing_set(idx + 1)
                        curr_set = self.get_containing_set(idx)

                        if not self.visited.get(tuple(next_set), None):
                            step['next'] = next_set
                            for nsa in next_set:
                                self.steps[nsa]['needs'] = id
                            self.visited[tuple(curr_set)] = True

        # Finally, generate the root.
        for a_id, a_block in self.steps.items():
            if not a_block.get('needs', None):
                self.root.add(a_id)


VALID_WORKFLOW_ATTRS = ["resolves", "on"]


class HCLWorkflow(Workflow):
    """Parse a hcl based workflow and generate
    the workflow graph.
    """

    def __init__(self, wfile):
        """Loads the workflow as a dict from the `.workflow` file."""
        super(HCLWorkflow, self).__init__()
        self.wf_fmt = "hcl"

        if not os.path.exists(wfile):
            # try to load a string
            self.wf_dict = hcl.loads(wfile)
        else:
            with open(wfile) as fp:
                self.wf_dict = hcl.load(fp)

        if 'action' in self.wf_dict:
            self.wf_dict['steps'] = self.wf_dict.pop('action')

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
            if self.steps[node].get('needs', None):
                for n in self.steps[node]['needs']:
                    self.find_root([n], root)
                    if not self.steps[n].get('next', None):
                        self.steps[n]['next'] = set()
                    self.steps[n]['next'].add(node)
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
            self.steps = self.wf_dict['steps']
            self.props = dict()

            if pu.of_type(self.resolves, ['str']):
                self.resolves = [self.resolves]

        for a_name, a_block in self.steps.items():
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
