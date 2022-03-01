from datetime import datetime
from typing import Optional, List

import click
from xlwt import Workbook, Worksheet, XFStyle, Font, Borders, Alignment, Formula  # type: ignore

from cars.domain.data_collectors.collectors import CarsParser


@click.group("collecting")
def collecting_group() -> None:
    """
    Tasks for collecting data from the web.
    """
    pass


@collecting_group.command("collect")
def collect() -> None:
    """
    Collect data for cars from ads.

    Example:

        cars collecting collect

        Will collect cars data and store it at `output/{current_date}.xls`.
    """
    from cars.config import cars_config
    from cars.exceptions import ApiRequestError, ProjectError

    data_collector = DataCollector()

    for car in sorted(cars_config.cars, key=lambda x: (x.brand, x.model)):
        generations = car.generations or [""]
        for generation in sorted(generations):
            click.echo(f"Collecting data for {car.brand} {car.model}", nl=False)
            if generation:
                click.echo(f" {generation}", nl=False)
            click.echo(nl=True)
            try:
                data_collector.add_car_data(car.brand, car.model, generation, car.body_types)
            except ApiRequestError as ex:
                click.echo(ex)
            except ProjectError as ex:
                click.echo(ex)

    current_time = datetime.now()
    current_time = current_time.replace(microsecond=0)
    filename = f"dumps/{current_time.strftime('%Y-%m-%d.%H-%M-%S')}.xls"
    click.echo(filename)
    data_collector.save(filename)


class DataCollector:
    def __init__(self):
        self.wb = Workbook()
        self.main_sheet: Worksheet = self.wb.add_sheet("Общее")
        self.style = XFStyle()
        self.header_style = XFStyle()
        bold_font = Font()
        bold_font.bold = True
        regular_font = Font()
        regular_font.bold = False
        borders = Borders()
        borders.top = Borders.THIN
        borders.bottom = Borders.THIN
        borders.left = Borders.THIN
        borders.right = Borders.THIN
        regular_alignment = Alignment()
        regular_alignment.horz = Alignment.HORZ_LEFT
        regular_alignment.vert = Alignment.VERT_CENTER
        header_alignment = Alignment()
        header_alignment.horz = Alignment.HORZ_CENTER
        header_alignment.vert = Alignment.VERT_CENTER
        self.style.borders = borders
        self.style.alignment = regular_alignment
        self.style.font = regular_font
        self.header_style.borders = borders
        self.header_style.alignment = header_alignment
        self.header_style.font = bold_font

        for column_id, name in enumerate(
            ("Производитель", "Модель", "Поколение", "Год от", "Год до", "Мин цена", "Макс цена"),
        ):
            self.main_sheet.write(0, column_id, name, self.header_style)

        self.first_brand_match = None
        self.first_model_match = None
        self.last_brand_value = None
        self.last_model_value = None

    def add_car_data(self, brand: str, model: str, generation: str, body_types: Optional[List[str]]) -> None:
        parser = CarsParser(brand, model, generation, body_types)
        car_data = parser.car_data

        sheet_name = f"{brand} {model}"
        if generation:
            sheet_name += f" {generation.replace('· ', '')}"
        if len(sheet_name) > 31:
            sheet_name = sheet_name.replace("Рестайлинг", "Рест")
        sheet: Worksheet = self.wb.add_sheet(sheet_name)
        for column_id, column_name in enumerate(CarsParser.columns_order):
            sheet.write(0, column_id, column_name, self.header_style)
        for data in sorted(car_data, key=lambda x: (x[4], x[3])):
            row_id = sheet.last_used_row + 1
            for column_id, val in enumerate(data):
                if column_id == 2:
                    assert isinstance(val, str)
                    val = Formula(f'HYPERLINK("{val}";"{val.split("/")[-1]}")')
                sheet.write(row_id, column_id, val, self.style)

        min_price = min(data[0] for data in car_data)
        max_price = max(data[0] for data in car_data)
        min_year = min(data[1] for data in car_data)
        max_year = max(data[1] for data in car_data)
        main_sheet_row = self.main_sheet.last_used_row + 1
        for column_id, val in enumerate(
            (brand, model, generation, min_year, max_year, min_price, max_price),
        ):
            if val is None:
                continue
            if column_id == 0:
                # is brand
                if self.first_brand_match is None:
                    self.first_brand_match = main_sheet_row
                    self.last_brand_value = val
                else:
                    if self.last_brand_value == val:
                        continue
                    self.main_sheet.write_merge(
                        self.first_brand_match,
                        main_sheet_row - 1,
                        column_id,
                        column_id,
                        self.last_brand_value,
                        self.style,
                    )
                    self.first_brand_match = main_sheet_row
                    self.last_brand_value = val
            elif column_id == 1:
                # is model
                if self.first_model_match is None:
                    self.first_model_match = main_sheet_row
                    self.last_model_value = val
                else:
                    if self.last_model_value == val:
                        continue
                    self.main_sheet.write_merge(
                        self.first_model_match,
                        main_sheet_row - 1,
                        column_id,
                        column_id,
                        self.last_model_value,
                        self.style,
                    )
                    self.first_model_match = main_sheet_row
                    self.last_model_value = val
            else:
                self.main_sheet.write(main_sheet_row, column_id, val, self.style)

    def save(self, filename):
        if self.first_brand_match is not None:
            self.main_sheet.write_merge(
                self.first_brand_match,
                self.main_sheet.last_used_row,
                0,
                0,
                self.last_brand_value,
                self.style,
            )

        if self.first_model_match is not None:
            self.main_sheet.write_merge(
                self.first_model_match,
                self.main_sheet.last_used_row,
                1,
                1,
                self.last_model_value,
                self.style,
            )
        self.wb.save(filename)
