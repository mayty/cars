import click
from cars.cli.collector import collecting_group


@click.group()
def cli_root() -> None:
    pass


cli_root.add_command(collecting_group)
