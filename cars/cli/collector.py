import click


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
    from cars.domain.data_collectors.collectors import CarsParser
    from cars.exceptions import ApiRequestError, ProjectError
    from xlwt import Workbook, Worksheet, easyxf, Formula, XFStyle, Font, Borders, Alignment  # type: ignore
    import datetime

    wb = Workbook()
    main_sheet: Worksheet = wb.add_sheet("Общее")
    style = XFStyle()
    header_style = XFStyle()
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
    style.borders = borders
    style.alignment = regular_alignment
    style.font = regular_font
    header_style.borders = borders
    header_style.alignment = header_alignment
    header_style.font = bold_font

    for column_id, name in enumerate(
        ("Производитель", "Модель", "Поколение", "Год от", "Год до", "Мин цена", "Макс цена"),
    ):
        main_sheet.write(0, column_id, name, header_style)

    first_brand_match = None
    first_model_match = None
    last_brand_value = None
    last_model_value = None
    for car in sorted(cars_config.cars, key=lambda x: (x.brand, x.model, x.generation)):
        try:
            print(f"Collecting data for {car.brand} {car.model}", end="")
            if car.generation is not None:
                print(f" {car.generation}", end="")
            print()
            parser = CarsParser(car.brand, car.model, car.generation)
            car_data = parser.car_data

            sheet_name = f"{car.brand} {car.model}"
            if car.generation:
                sheet_name += f" {car.generation.replace('· ', '')}"
            if len(sheet_name) > 31:
                sheet_name = sheet_name.replace("Рестайлинг", "Рест")
            sheet: Worksheet = wb.add_sheet(sheet_name)
            for column_id, column_name in enumerate(CarsParser.columns_order):
                sheet.write(0, column_id, column_name, header_style)
            for data in sorted(car_data, key=lambda x: (x[4], x[3])):
                row_id = sheet.last_used_row + 1
                for column_id, val in enumerate(data):
                    if column_id == 2:
                        assert isinstance(val, str)
                        val = Formula(f'HYPERLINK("{val}";"{val.split("/")[-1]}")')
                    sheet.write(row_id, column_id, val, style)

            min_price = min(data[0] for data in car_data)
            max_price = max(data[0] for data in car_data)
            min_year = min(data[1] for data in car_data)
            max_year = max(data[1] for data in car_data)
            main_sheet_row = main_sheet.last_used_row + 1
            for column_id, val in enumerate(
                (car.brand, car.model, car.generation, min_year, max_year, min_price, max_price),
            ):
                if val is None:
                    continue
                if column_id == 0:
                    # is brand
                    if first_brand_match is None:
                        first_brand_match = main_sheet_row
                        last_brand_value = val
                    else:
                        if last_brand_value == val:
                            continue
                        main_sheet.write_merge(
                            first_brand_match,
                            main_sheet_row - 1,
                            column_id,
                            column_id,
                            last_brand_value,
                            style,
                        )
                        first_brand_match = main_sheet_row
                        last_brand_value = val
                elif column_id == 1:
                    # is model
                    if first_model_match is None:
                        first_model_match = main_sheet_row
                        last_model_value = val
                    else:
                        if last_model_value == val:
                            continue
                        main_sheet.write_merge(
                            first_model_match,
                            main_sheet_row - 1,
                            column_id,
                            column_id,
                            last_model_value,
                            style,
                        )
                        first_model_match = main_sheet_row
                        last_model_value = val
                else:
                    main_sheet.write(main_sheet_row, column_id, val, style)
        except ApiRequestError as ex:
            click.echo(ex)
        except ProjectError as ex:
            click.echo(ex)

    if first_brand_match is not None:
        main_sheet.write_merge(
            first_brand_match,
            main_sheet.last_used_row,
            0,
            0,
            last_brand_value,
            style,
        )

    if first_model_match is not None:
        main_sheet.write_merge(
            first_model_match,
            main_sheet.last_used_row,
            1,
            1,
            last_model_value,
            style,
        )
    current_time = datetime.datetime.now()
    current_time = current_time.replace(microsecond=0)
    filename = f"dumps/{current_time.strftime('%Y-%m-%d.%H-%M-%S')}.xls"
    click.echo(filename)
    wb.save(filename)
