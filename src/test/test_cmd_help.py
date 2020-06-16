from click.testing import CliRunner
import click
from click import Context

from popper.commands import cmd_help
from .test_common import PopperTest
from popper.cli import PopperCLI, cmd_folder


class TestCommandHelp(PopperTest):
    def test_help(self):
        popper_cli = PopperCLI()
        subcommands = popper_cli.list_commands(click.Context(popper_cli))

        help_texts = []
        with self.assertLogs("popper") as test:
            runner = CliRunner()
            for subcommand in subcommands:
                result = runner.invoke(cmd_help.cli, [subcommand])
                self.assertEqual(result.exit_code, 0)
                target_command = popper_cli.get_command(
                    click.Context(popper_cli), subcommand
                )
                help_texts.append(target_command.get_help(click.Context(popper_cli)))

        for command_output, test_output in zip(help_texts, test.output):
            self.assertIn(
                command_output.replace(" ", "").replace("\n", ""),
                test_output.replace(" ", "").replace("\n", ""),
            )
