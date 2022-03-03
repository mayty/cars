import click
from cars.cli.collector import collecting_group
from cars.cli.collector_google import collecting_group as google_collecting_group


@click.group()
def cli_root() -> None:
    pass


cli_root.add_command(collecting_group)
cli_root.add_command(google_collecting_group)
