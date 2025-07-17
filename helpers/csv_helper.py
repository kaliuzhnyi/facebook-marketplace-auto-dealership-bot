import csv
import dataclasses
from dataclasses import asdict
from enum import Enum

from config import CONFIG
from helpers.model import VehicleType, BodyType, BaseColor, FuelType, VehicleCondition, Transmission, Listing


def get_data_from_csv(file_path: str = CONFIG['data']['path']) -> list[Listing]:
    rows = []
    with open(file_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row_dict in reader:
            if not any(value.strip() for value in row_dict.values() if value):
                continue
            rows.append(Listing(
                photos_folder=row_dict.get('photos_folder', ''),
                photos_names=row_dict.get('photos_names', '').split(";"),
                vehicle_type=VehicleType.from_str(row_dict.get('vehicle_type', '')),
                vehicle_condition=VehicleCondition.from_str(row_dict.get('vehicle_condition', '')),
                body_type=BodyType.from_str(row_dict.get('body_type', '')),
                year=row_dict.get('year', ''),
                make=row_dict.get('make', ''),
                model=row_dict.get('model', ''),
                exterior_color=BaseColor.from_str(row_dict.get('exterior_color', '')),
                interior_color=BaseColor.from_str(row_dict.get('interior_color', '')),
                mileage=int(row_dict.get('mileage', '0')),
                fuel_type=FuelType.from_str(row_dict.get('fuel_type', '')),
                transmission=Transmission.from_str(row_dict.get('transmission', '')),
                price=float(row_dict.get('price', '')),
                title=row_dict.get('title', ''),
                description=row_dict.get('description', ''),
                location=row_dict.get('location', ''),
                groups=row_dict.get('groups', '').split(";"),
                stockno=row_dict.get('stockno', ''),
                vin=row_dict.get('vin', '')
            ))
    return rows


def push_data_to_csv(rows: list[Listing],
                     file_path: str = CONFIG['data']['path'],
                     upload_limit: int = CONFIG['data']['upload_limit']):
    if not rows:
        return

    fieldnames = [f.name for f in dataclasses.fields(rows[0])]

    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        i = 0
        for row in rows:
            if i >= upload_limit:
                break

            data = asdict(row)
            for key, value in data.items():
                if isinstance(value, Enum):
                    data[key] = value.value
                elif isinstance(value, list):
                    data[key] = ";".join(value)
            writer.writerow(data)
            i += 1
