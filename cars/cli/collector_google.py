import click
import httplib2
from googleapiclient.discovery import build, Resource
from oauth2client.service_account import ServiceAccountCredentials


@click.group("google_collecting")
def collecting_group() -> None:
    """
    Tasks for collecting data from the web.
    """
    pass


def get_service_account(path: str):
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds_service = ServiceAccountCredentials.from_json_keyfile_name(path, scopes).authorize(httplib2.Http())
    return build('sheets', 'v4', http=creds_service)


@collecting_group.command('collect')
def collect():
    from os import environ
    sheet_id = '1uTYVXJ9pXDXevOD0TAnq3eKj1XDd-DXAdgv2yKzdJi4'
    credentials_json_path = environ.get('TOKEN_PATH')
    if not credentials_json_path:
        click.echo('Environment variable TOKEN_PATH must be set')
        return
    click.echo(credentials_json_path)
    service = get_service_account(credentials_json_path)
    sheet: Resource = service.spreadsheets()

    data = {
        'valueInputOption': 'RAW',
        'data': [
            {'range': f'Sheet5!A1', 'values': [[1,2,3]]},
            {'range': f'Sheet5!A2', 'values': [[2,3,4]]},
        ],
    }
    resp = sheet.values().batchUpdate(spreadsheetId=sheet_id, body=data).execute()
    click.echo(resp)
