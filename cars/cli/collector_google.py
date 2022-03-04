from typing import Optional

import click


@click.group("google_collecting")
def collecting_group() -> None:
    """
    Tasks for collecting data from the web.
    """
    pass


@collecting_group.command("collect")
@click.option(
    "--spreadsheet-id",
    "-s",
    "spreadsheet_id",
    type=str,
)
def collect(spreadsheet_id: Optional[str] = None):
    from os import environ
    from cars.cli.helpers import collect_to_gsheet

    if not spreadsheet_id:
        spreadsheet_id = environ.get("SPREADSHEET_ID")
        if not spreadsheet_id:
            click.echo("One of spreadsheet_id option and SPREADSHEET_ID environment variable must be provided.")
            return
    credentials_json_path = environ.get("TOKEN_PATH")
    if not credentials_json_path:
        click.echo("Environment variable TOKEN_PATH must be set")
        return
    click.echo(credentials_json_path)
    collect_to_gsheet(spreadsheet_id, credentials_json_path, click.echo)
