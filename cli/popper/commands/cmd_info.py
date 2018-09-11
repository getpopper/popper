import click
import popper.utils as pu
import sys

from popper.cli import pass_context
from popper.exceptions import BadArgumentUsage


@click.command(
    'info', short_help='Show details about a pipeline hosted on github.'
)
@click.argument('pipeline', required=True)
@click.option('--full', help=('Show full content of README'), is_flag=True)
@click.option(
    '--update-cache',
    help=('Update the pipeline metadata cache prior to looking for info'),
    default=False,
    is_flag=True
)
@pass_context
def cli(ctx, pipeline, full, update_cache):
    """Displays the description of a pipeline hosted on Github. The
    format for specifying pipelines is <org>/<repo>/<pipeline>. For example:

      popper info popperized/quiho-popper/single-node

    By default, this command searches information from the pipeline metadata
    cache. To recreate it (fetch from Github), pass the --update-cache flag.
    """
    orgrepopipe = pipeline.split('/')

    if len(orgrepopipe) != 3:
        raise BadArgumentUsage(
                "Bad name format. See 'popper info --help' for more info.")

    org, repo, name = orgrepopipe[0:]

    meta = pu.fetch_pipeline_metadata(skip_update=(not update_cache))

    pipe_meta = meta[org][repo]['pipelines'].get(name, None)

    if not pipe_meta:
        pu.fail('Unable to find metadata for given pipeline')

    if not pipe_meta['readme']:
        pu.info('This pipeline does not have a README file associated with it')
        sys.exit(0)

    pu.info('')

    if full:
        pu.info(pipe_meta['readme'])
    else:
        readme_lines = pipe_meta['readme'].split('\n')
        if len(readme_lines) <= 2:
            pu.info(pipe_meta['readme'])
        else:
            for l in readme_lines[2:]:
                if not l:
                    break
                pu.info(l)
    pu.info('')
