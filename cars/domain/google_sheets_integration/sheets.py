from typing import Dict, Union, List

from googleapiclient.discovery import build, Resource  # type: ignore
from httplib2 import Http  # type: ignore
from oauth2client.service_account import ServiceAccountCredentials  # type: ignore

from cars.domain.google_sheets_integration.operations import Operation


class SheetsRequests:
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds_service = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scopes).authorize(Http())
        service = build("sheets", "v4", http=creds_service)
        self.spreadsheets: Resource = service.spreadsheets()
        self.operations: List[Operation] = []
        self.spreadsheet_id = spreadsheet_id

    def add_operation(self, operation: Operation) -> None:
        self.operations.append(operation)

    def execute(self):
        data = {
            "requests": [operation.to_dict() for operation in self.operations],
            "includeSpreadsheetInResponse": False,
        }
        self.spreadsheets.batchUpdate(spreadsheetId=self.spreadsheet_id, body=data).execute()

    def get_sheets_data(self) -> Dict[str, Dict[str, Union[int, bool]]]:
        resp = self.spreadsheets.get(spreadsheetId=self.spreadsheet_id).execute()
        return {
            sheet["properties"]["title"]: {
                "id": sheet["properties"]["sheetId"],
                "used": False,
            }
            for sheet in resp["sheets"]
        }
