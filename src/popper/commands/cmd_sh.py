import click
import traceback

from popper.cli import pass_context, log
from popper.config import ConfigLoader
from popper.parser import WorkflowParser
from popper.runner import WorkflowRunner


@click.command("sh", short_help="Start an interactive shell for the given step.")
@click.argument("step", required=True)
@click.option(
    "-f",
    "--file",
    help="File containing the definition of the workflow.",
    required=False,
    default=".popper.yml",
)
@click.option(
    "-e",
    "--entrypoint",
    help="Shell program to invoke.",
    required=False,
    default="/bin/bash",
)
@pass_context
def cli(ctx, file, step, entrypoint):
    """Opens an interactive shell using all the attributes defined in the workflow file
    for the given STEP, but ignoring ``runs`` and ``args``. By default, it invokes
    /bin/bash. If you need to invoke another one, you can specify it in the --entrypoint
    flag.

    NOTE: this command only works for (local) host runner in Docker.
    """
    wf = WorkflowParser.parse(file=file, step=step, immutable=False)

    # override entrypoint
    step = wf.steps[0]
    step.args = []
    step.runs = entrypoint

    # configure runner so containers execute in attached mode and create a tty
    config = ConfigLoader.load(engine_name="docker", pty=True)

    with WorkflowRunner(config) as runner:
        try:
            runner.run(wf)
        except Exception as e:
            log.debug(traceback.format_exc())
            log.fail(e)
