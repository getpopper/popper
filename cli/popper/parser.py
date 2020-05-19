from __future__ import unicode_literals

import logging
import os
import re
import yaml

from popper.cli import log as log

from box import Box

from pykwalify.core import Core as YMLValidator
from pykwalify.errors import SchemaError


class WorkflowParser(object):
    _wf_schema = {
        "type": "map",
        "mapping": {
            "steps": {
                "type": "seq",
                "sequence": [
                    {
                        "type": "map",
                        "mapping": {
                            "uses": {"type": "str", "required": True},
                            "id": {"type": "str"},
                            "args": {"type": "seq", "sequence": [{"type": "str"}]},
                            "runs": {"type": "seq", "sequence": [{"type": "str"}]},
                            "secrets": {"type": "seq", "sequence": [{"type": "str"}]},
                            "skip_pull": {"type": "bool"},
                            "env": {
                                "type": "map",
                                "matching-rule": "any",
                                "mapping": {"regex;(.+)": {"type": "str"}},
                            },
                        },
                    }
                ],
            },
            "options": {
                "type": "map",
                "mapping": {
                    "secrets": {"type": "seq", "sequence": [{"type": "str"}]},
                    "env": {
                        "type": "map",
                        "matching-rule": "any",
                        "mapping": {"regex;(.+)": {"type": "str"}},
                    },
                },
            },
        },
    }

    @staticmethod
    def parse(
        file=None,
        wf_data=None,
        step=None,
        skipped_steps=[],
        substitutions=[],
        allow_loose=False,
    ):
        """Returns an immutable workflow structure (a frozen Box) with 'steps' and
        'options' properties. See WorkflowParser._wf_schema above for their structure.
        """

        if not file and not wf_data:
            log.fail("Expecting 'file' or 'wf_data'")

        if file:
            if wf_data:
                log.fail("Expecting only one of 'file' and 'wf_data'")

            if not os.path.exists(file):
                log.fail(f"File {file} was not found.")

            if not file.endswith(".yml") and not file.endswith(".yaml"):
                log.fail("Unrecognized workflow file format.")

            with open(file, "r") as f:
                _wf_data = yaml.safe_load(f)

                if not _wf_data:
                    log.fail(f"File {file} is empty")
        else:
            _wf_data = wf_data

        # hack to silence warnings about error to fail change
        logging.disable(logging.CRITICAL)

        v = YMLValidator(source_data=_wf_data, schema_data=WorkflowParser._wf_schema)

        try:
            v.validate()
        except SchemaError as e:
            log.fail(f"{e.msg}")

        logging.disable(logging.NOTSET)

        WorkflowParser.__add_missing_ids(_wf_data)
        WorkflowParser.__propagate_options_to_steps(_wf_data)
        WorkflowParser.__apply_substitutions(
            _wf_data, substitutions=substitutions, allow_loose=allow_loose
        )
        WorkflowParser.__skip_steps(_wf_data, skipped_steps)
        WorkflowParser.__filter_step(_wf_data, step)

        # create and frozen a box
        wf_box = Box(_wf_data, frozen_box=True, default_box=True)

        log.debug(f"Parsed workflow:\n{wf_box}")

        return wf_box

    @staticmethod
    def __apply_substitution(wf_element, k, v, used_registry):
        if isinstance(wf_element, str):
            if k in wf_element:
                wf_element.replace(k, v)
                used_registry[k] = 1

        elif isinstance(wf_element, list):
            # we assume list of strings
            for i, e in enumerate(wf_element):
                if k in e:
                    wf_element[i].replace(k, v)
                    used_registry[k] = 1

        elif isinstance(wf_element, dict):
            # we assume list of strings
            for ek in wf_element:
                if k in ek:
                    log.fail("Substitutions only allowed on keys of dictionaries")
                if k in wf_element[ek]:
                    wf_element[ek].replace(k, v)
                    used_registry[k] = 1

    @staticmethod
    def __add_missing_ids(wf_data):
        for i, step in enumerate(wf_data["steps"]):
            step["id"] = step.get("id", f"{i+1}")

    @staticmethod
    def __propagate_options_to_steps(wf_data):
        """Copies env and secrets attributes from 'options' to each step. Step
        attributes have precedence over workflow-wide ones
        """
        # we create dict/list with env/secrets from 'options'
        wf_env = wf_data.get("options", {}).get("env", {})
        wf_secrets = wf_data.get("options", {}).get("secrets", [])

        # for each step, create a copy of the above, and update with info from step in
        # order to make step have higher precedence over workflow-wide options
        for i, step in enumerate(wf_data["steps"]):
            step_env = dict(wf_env)
            step_env.update(step.get("env", {}))
            step["env"] = step_env

            step_secrets = wf_secrets + step.get("secrets", [])
            step["secrets"] = step_secrets

    @staticmethod
    def __apply_substitutions(wf_data, substitutions=None, allow_loose=False):
        if not substitutions:
            return

        used = {}
        for substitution in substitutions:
            item = substitution.split("=", 1)
            if len(item) < 2:
                raise Exception("Excepting '=' as seperator")

            k, v = ("$" + item[0], item[1])

            if not re.match(r"\$_[A-Z0-9]+", k):
                log.fail(f"Expecting substitution key as $_[A-Z0-9] but got '{k}'.")

            # replace in steps
            for step in wf_data["steps"]:
                for _, step_attr in step.items():
                    Workflow._apply_substitution(step_attr, k, v, used)

            for _, options_attr in wf_data.get("options", {}).items():
                Workflow._apply_substitution(options_attr, k, v, used)

        if not allow_loose and len(substitutions) != len(used):
            log.fail("Not all given substitutions are used in " "the workflow file")

    @staticmethod
    def __skip_steps(wf_data, skip_list=[]):
        if not skip_list:
            return
        filtered_list = []
        used = {}
        for step in wf_data["steps"]:
            if step["id"] in skip_list:
                used[step["id"]] = 1
                continue
            filtered_list.append(step)
        wf_data["steps"] = filtered_list

        if len(used) != len(skip_list):
            log.fail(f"Not all skipped steps exist in the workflow.")

    @staticmethod
    def __filter_step(wf_data, filtered_step=None):
        """Remove all but the given one."""
        if not filtered_step:
            return
        for step in wf_data["steps"]:
            if step["id"] == filtered_step:
                return step
