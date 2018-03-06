import click
import os
import popper.utils as pu

from popper.cli import pass_context
from popper.exceptions import BadArgumentUsage

@click.command('stages', short_help='Comma-separated list of stages to a pipeline')
@click.argument('pipeline', required=True)
@click.option(
    '--set',
    help="Redefine the stages of a pipeline",
    required=False
)
@pass_context
def cli(ctx, pipeline, set):
    """Manipulates the stages of a pipeline.The stages YAML entry specifies
    the sequence of stages that are executed by the popper check command.When
    a new pipeline is created, the popper init generates scaffold scripts for
    setup.sh,run.sh,post-run.sh,validate.sh,teardown.sh by default.(See popper
    init --help for more)

    Example:

    popper stages #Shows the stages of a pipeline

    popper stages --set=one,two,three #Redefine the stages of a pipeline
    """
    config = pu.read_config()

    if not set:
        pu.print_yaml(str(config['pipelines'][pipeline]['stages']))

    if set:
        for s in stages.split(','):
            s_filename = os.path.join(pipeline_path, s)
            if not os.path.isfile(s_filename) and not os.path.isfile(s_filename+'.sh'):
                pu.fail("Unable to find script for stage " + s +
                ". You might need to provide values for the --set flag.")

        if 'teardown' in stages and stages.split(',')[-1] != 'teardown' :
            raise BadArgumentUsage('--stages = Teardown should be the last stage.'
        + ' Consider renaming it or putting it at the end.')

        config['pipelines'][pipeline]['stages'] = stages.split(',')

    pu.write_config(config)
