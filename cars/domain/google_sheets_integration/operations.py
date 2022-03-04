from copy import deepcopy
from typing import Dict, Any, List


class Operation:
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError()


class AddSheet(Operation):
    def __init__(self, title: str, id_: int) -> None:
        self.title = title
        self.id = id_

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"addSheet": {"properties": {}}}
        if self.title is not None:
            result["addSheet"]["properties"]["title"] = self.title
        if self.id is not None:
            result["addSheet"]["properties"]["sheetId"] = self.id
        return result


class DeleteSheet(Operation):
    def __init__(self, id_: int) -> None:
        self.id = id_

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deleteSheet": {
                "sheetId": self.id,
            },
        }


class ClearSheet(Operation):
    def __init__(self, id_: int) -> None:
        self.id = id_

    def to_dict(self) -> Dict[str, Any]:
        return {
            "updateCells": {
                "rows": [],
                "fields": "*",
                "range": {
                    "sheetId": self.id,
                },
            }
        }


class ChangeBorder(Operation):
    def __init__(self, id_: int, x0: int, w: int, y0: int, h: int):
        self.id = id_
        self.x0 = x0
        self.w = w
        self.y0 = y0
        self.h = h

    def to_dict(self) -> Dict[str, Any]:
        return {
            "updateBorders": {
                "range": {
                    "sheetId": self.id,
                    "startRowIndex": self.y0,
                    "endRowIndex": self.y0 + self.h,
                    "startColumnIndex": self.x0,
                    "endColumnIndex": self.x0 + self.w,
                },
                "top": {"style": "SOLID"},
                "bottom": {"style": "SOLID"},
                "left": {"style": "SOLID"},
                "right": {"style": "SOLID"},
                "innerHorizontal": {"style": "SOLID"},
                "innerVertical": {"style": "SOLID"},
            }
        }


class WriteData(Operation):
    def __init__(self, id_: int, values: List[List[Any]]) -> None:
        self.id = id_
        self.values = values

    def _values_to_rows(self, values: List[List[Any]]) -> List[Dict[str, Any]]:
        return [{"values": self._row_to_cells(row, i == 0)} for i, row in enumerate(values)]

    def _row_to_cells(self, row: List[Any], is_header: bool) -> List[Dict[str, Any]]:
        return [self._value_to_cell(value, is_header) for value in row]

    def _value_to_cell(self, value: Any, is_header: bool) -> Dict[str, Any]:
        header_style = {
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "textFormat": {
                "bold": True,
            },
        }
        regular_style = {
            "horizontalAlignment": "LEFT",
            "verticalAlignment": "MIDDLE",
            "textFormat": {
                "bold": False,
            },
        }

        current_style = deepcopy(header_style if is_header else regular_style)
        serialized_value = self._serialize_value(value)
        return {
            "userEnteredValue": {"formulaValue": serialized_value}
            if serialized_value.startswith("=")
            else {"stringValue": serialized_value},
            "userEnteredFormat": current_style,
        }

    def _serialize_value(self, value: Any) -> str:
        if not isinstance(value, str):
            return str(value)
        if value.startswith("https://"):
            return f'=HYPERLINK("{value}", {value.split("/")[-1]})'
        return value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "updateCells": {
                "rows": self._values_to_rows(self.values),
                "fields": "*",
                "start": {
                    "sheetId": self.id,
                    "rowIndex": 0,
                    "columnIndex": 0,
                },
            }
        }


class MergeCells(Operation):
    def __init__(self, id_: int, row_id: int, height: int, column_id: int):
        self.id = id_
        self.row_id = row_id
        self.height = height
        self.column_id = column_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mergeCells": {
                "range": {
                    "sheetId": self.id,
                    "startRowIndex": self.row_id,
                    "endRowIndex": self.row_id + self.height + 1,
                    "startColumnIndex": self.column_id,
                    "endColumnIndex": self.column_id + 1,
                },
                "mergeType": "MERGE_ALL",
            }
        }


class UnmergeAllCells(Operation):
    def __init__(self, id_: int):
        self.id = id_

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unmergeCells": {
                "range": {
                    "sheetId": self.id,
                }
            }
        }


class ResizeColumns(Operation):
    def __init__(self, id_: int):
        self.id = id_

    def to_dict(self) -> Dict[str, Any]:
        return {
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": self.id,
                    "dimension": "COLUMNS",
                }
            }
        }
