from typing import Optional, List, Any

import click

from cars.config import cars_config
from cars.domain.data_collectors.collectors import CarsParser
from cars.domain.google_sheets_integration.operations import (
    AddSheet,
    ClearSheet,
    WriteData,
    ChangeBorder,
    ResizeColumns,
    DeleteSheet,
    MergeCells,
)
from cars.domain.google_sheets_integration.sheets import SheetsRequests
from cars.exceptions import ApiRequestError, ProjectError


@click.group("google_collecting")
def collecting_group() -> None:
    """
    Tasks for collecting data from the web.
    """
    pass


def get_merge_operations(sheet_id: int, sheet_values: List[List[Any]], column_id) -> List[MergeCells]:
    operations = []
    start_i = 1
    length = 0
    last_val = None
    for i, summary_row in enumerate(sheet_values[1:]):
        value = summary_row[column_id]
        if last_val and value == last_val:
            length += 1
            continue

        if length > 0:
            operations.append(
                MergeCells(
                    sheet_id,
                    start_i,
                    length,
                    column_id,
                )
            )

        start_i = i + 1
        last_val = value
        length = 0

    if length > 0:
        operations.append(
            MergeCells(
                sheet_id,
                start_i,
                length,
                column_id,
            )
        )
    return operations


@collecting_group.command("collect")
@click.option(
    "--spreadsheet-id",
    "-s",
    "spreadsheet_id",
    type=str,
)
def collect(spreadsheet_id: Optional[str] = None):
    from os import environ

    if not spreadsheet_id:
        spreadsheet_id = environ.get("SPREADSHEET_ID")
        if not spreadsheet_id:
            click.echo("One of spreadsheet_id option and SPREADSHEET_ID environment variable must be provided.")
            return
    sheet_id = "1iZXe2sZ4tn5JFqKTszqoNQVN2SOGQhA2HUC7U8I44lg"
    credentials_json_path = environ.get("TOKEN_PATH")
    if not credentials_json_path:
        click.echo("Environment variable TOKEN_PATH must be set")
        return
    click.echo(credentials_json_path)

    requests = SheetsRequests(credentials_json_path, sheet_id)
    sheets_data = requests.get_sheets_data()
    main_sheet_name = "Summary"

    next_sheet_id = max(data["id"] for data in sheets_data.values()) + 1

    if main_sheet_name not in sheets_data:
        sheets_data[main_sheet_name] = {
            "id": next_sheet_id,
            "used": True,
        }
        requests.add_operation(AddSheet(main_sheet_name, next_sheet_id))
        next_sheet_id += 1
    else:
        requests.add_operation(ClearSheet(sheets_data[main_sheet_name]["id"]))
        sheets_data[main_sheet_name]["used"] = True

    new_summary_values: List[List[Any]] = [
        [
            "Производитель",
            "Модель",
            "Поколение",
            "Год от",
            "Год до",
            "Мин цена",
            "Макс цена",
        ]
    ]

    for car in sorted(cars_config.cars, key=lambda x: (x.brand, x.model)):
        generations = car.generations or [""]
        for generation in sorted(generations):
            sheet_name = f"{car.brand} {car.model}"
            if generation:
                sheet_name += f" {generation}"

            click.echo(sheet_name)

            try:
                parser = CarsParser(car.brand, car.model, generation, car.body_types)
                columns_order = parser.columns_order
                car_data = parser.car_data
            except ApiRequestError as ex:
                click.echo(ex)
                continue
            except ProjectError as ex:
                click.echo(ex)
                continue

            if sheet_name not in sheets_data:
                sheets_data[sheet_name] = {
                    "id": next_sheet_id,
                    "used": True,
                }
                requests.add_operation(AddSheet(sheet_name, next_sheet_id))
            else:
                requests.add_operation(ClearSheet(sheets_data[sheet_name]["id"]))
                sheets_data[sheet_name]["used"] = True
            new_spreadsheet_data = [list(columns_order)]

            for ad_data in sorted(car_data, key=lambda x: (x[4], x[3])):
                new_spreadsheet_data.append(list(ad_data))

            new_summary_values.append(
                [
                    car.brand,
                    car.model,
                    generation,
                    min(data[1] for data in car_data),
                    max(data[1] for data in car_data),
                    min(data[0] for data in car_data),
                    max(data[0] for data in car_data),
                ]
            )

            requests.add_operation(WriteData(sheets_data[sheet_name]["id"], new_spreadsheet_data))
            requests.add_operation(
                ChangeBorder(sheets_data[sheet_name]["id"], 0, len(columns_order), 0, len(new_spreadsheet_data))
            )
            requests.add_operation(ResizeColumns(sheets_data[sheet_name]["id"]))
            next_sheet_id += 1

    requests.add_operation(WriteData(sheets_data[main_sheet_name]["id"], new_summary_values))
    requests.add_operation(
        ChangeBorder(sheets_data[main_sheet_name]["id"], 0, len(new_summary_values[0]), 0, len(new_summary_values))
    )
    requests.add_operation(ResizeColumns(sheets_data[main_sheet_name]["id"]))
    for operation in get_merge_operations(sheets_data[main_sheet_name]["id"], new_summary_values, 0):
        requests.add_operation(operation)
    for operation in get_merge_operations(sheets_data[main_sheet_name]["id"], new_summary_values, 1):
        requests.add_operation(operation)

    for data in sheets_data.values():
        if data["used"]:
            continue
        requests.add_operation(DeleteSheet(data["id"]))

    requests.execute()

    click.echo("Done")
