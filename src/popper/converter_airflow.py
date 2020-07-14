from airflow.models.baseoperator import BaseOperator
from airflow.utils.decorators import apply_defaults

from airflow import DAG

# from popper.config import ConfigLoader
from popper.parser import WorkflowParser

# from popper.runner import WorkflowRunner


class PopperOperator(BaseOperator):
    @apply_defaults
    def __init__(self, step_id: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.step_id = step_id

    def execute(self, context):
        pass
        # wf = WorkflowParser.parse(
        #     wfile,
        #     step=step,
        #     skipped_steps=skip,
        #     substitutions=substitution,
        #     allow_loose=allow_loose,
        # )

        # config = ConfigLoader.load(
        #     engine_name=engine,
        #     resman_name=resource_manager,
        #     config_file=conf,
        #     reuse=reuse,
        #     dry_run=dry_run,
        #     skip_pull=skip_pull,
        #     skip_clone=skip_clone,
        #     workspace_dir=workspace,
        # )

        # with WorkflowRunner(config) as runner:
        #     try:
        #         runner.run(wf)


def make_airflow_dag(dag_id, schedule_interval, default_args={}):
    for c in ["wf_file", "workspace_dir", "description"]:
        if default_args.get(c, None):
            raise ValueError(f"Expecting {c} in default_args")

    dag = DAG(dag_id, default_args=default_args, schedule_interval=schedule_interval)

    # parse workflow so we can iterate the steps
    wf = WorkflowParser.parse(default_args["wf_file"])

    tasks = []
    for step in wf.steps:
        # create an instance of a Popper operator for each step
        tasks.append(PopperOperator(step.id, **default_args))

    return dag, tasks
