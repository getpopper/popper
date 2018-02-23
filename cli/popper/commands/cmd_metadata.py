import click
import popper.utils as pu

from popper.cli import pass_context


@click.command('metadata', short_help='Modify metadata for a repo.')
@click.option(
    '--add',
    help="Add or overwrite metadata entry (in key=value format).",
    multiple=True,
    required=False
)
@click.option(
    '--rm',
    help="Key to remove from repository metadata.",
    multiple=True,
    required=False
)
@pass_context
def cli(ctx, add, rm):
    """Manipulates the metadata associated to a Popper repository. A metadata
    entry is an arbitrary key-value pair. Without any options, it displays all
    the existing metadata entries.

    Examples:

      popper metadata # show all entries

      popper metadata --add author='Jane Doe' --add year=2018

      popper metadata --rm author
    """
    config = pu.read_config()

    if not add and not rm:
        pu.info(str(config['metadata']))

    if add:
        for kv_str in add:
            kv_list = kv_str.split('=')
            config['metadata'][kv_list[0]] = kv_list[1]

    if rm:
        for k in rm:
            config['metadata'].pop(k)

    pu.write_config(config)
