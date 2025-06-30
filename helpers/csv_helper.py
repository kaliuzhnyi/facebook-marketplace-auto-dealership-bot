import csv
import os
from enum import Enum
from pathlib import Path

from config import CONFIG_PHOTOS_BASE_FOLDER


class VehicleType(str, Enum):
    CAR_TRUCK = 'Car/Track'
    MOTORCYCLE = 'Motorcycle'
    POWERSPORT = 'Powersport'
    RV_CAMPER = 'RV/Camper'
    TRAILER = 'Trailer'
    BOAT = 'Boat'
    COMMERCIAL_INDUSTRIAL = 'Commercial/Industrial'
    OTHER = 'Other'

    @classmethod
    def from_str(cls, label: str) -> 'VehicleType':
        for value in cls:
            if value.value.lower() == label.lower():
                return value
        return VehicleType.OTHER


class BodyType(str, Enum):
    COUPE = 'Coupe'
    TRUCK = 'Truck'
    SEDAN = 'Sedan'
    HATCHBACK = 'Hatchback'
    SUV = 'SUV'
    CONVERTIBLE = 'Convertible'
    WAGON = 'Wagon'
    MINIVAN = 'Minivan'
    SMALL_CAR = 'Small Car'
    OTHER = 'Other'

    @classmethod
    def from_str(cls, label: str) -> 'BodyType':
        for value in cls:
            if value.value.lower() == label.lower():
                return value
        return BodyType.OTHER


class BaseColor(str, Enum):
    BLACK = "Black"
    BLUE = "Blue"
    BROWN = "Brown"
    GOLD = "Gold"
    GREEN = "Green"
    GRAY = "Gray"
    PINK = "Pink"
    PURPLE = "Purple"
    RED = "Red"
    SILVER = "Silver"
    ORANGE = "Orange"
    WHITE = "White"
    YELLOW = "Yellow"
    CHARCOAL = "Charcoal"
    OFF_WHITE = "Off white"
    TAN = "Tan"
    BEIGE = "Beige"
    BURGUNDY = "Burgundy"
    TURQUOISE = "Turquoise"
    OTHER = "Other"

    @classmethod
    def from_str(cls, label: str) -> 'BaseColor':
        for value in cls:
            if value.value.lower() == label.lower():
                return value
        return BaseColor.OTHER


class FuelType(str, Enum):
    DIESEL = "Diesel"
    ELECTRIC = "Electric"
    GASOLINE = "Gasoline"
    FLEX = "Flex"
    HYBRID = "Hybrid"
    PETROL = "Petrol"
    PLUG_IN_HYBRID = "Plug-in hybrid"
    OTHER = "Other"

    @classmethod
    def from_str(cls, value: str):
        for item in cls:
            if item.value.lower() == value.lower():
                return item
        return FuelType.OTHER


class VehicleCondition(str, Enum):
    EXCELLENT = "Excellent"
    VERY_GOOD = "Very good"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"

    @classmethod
    def from_str(cls, value: str):
        if not value:
            return None
        for item in cls:
            if item.value.lower() == value.lower():
                return item
        return None


class Transmission(str, Enum):
    MANUAL = "Manual transmission"
    AUTOMATIC = "Automatic transmission"

    @classmethod
    def from_str(cls, value: str):
        for item in cls:
            if item.value.lower() == value.lower():
                return item
        if value.lower() == 'manual':
            return Transmission.MANUAL
        if value.lower() == 'automatic':
            return Transmission.AUTOMATIC
        return None


class Row:
    HEADER_PHOTOS_FOLDER = 'photos_folder'
    HEADER_PHOTOS_NAMES = 'photos_names'
    HEADER_VEHICLE_TYPE = 'vehicle_type'
    HEADER_VEHICLE_CONDITION = 'vehicle_condition'
    HEADER_YEAR = 'year'
    HEADER_MAKE = 'make'
    HEADER_MODEL = 'model'
    HEADER_EXTERIOR_COLOR = 'exterior_color'
    HEADER_INTERIOR_COLOR = 'interior_color'
    HEADER_MILEAGE = 'mileage'
    HEADER_FUEL_TYPE = 'fuel_type'
    HEADER_PRICE = 'price'
    HEADER_DESCRIPTION = 'description'
    HEADER_LOCATION = 'location'
    HEADER_GROUPS = 'groups'

    def __init__(self,
                 photos_folder: str = '',
                 photos_names: list[str] = None,
                 vehicle_type: str | VehicleType = VehicleType.CAR_TRUCK,
                 vehicle_condition: str | VehicleCondition | None = None,
                 body_type: str | BodyType = BodyType.SUV,
                 year: int | None = None,
                 make: str = '',
                 model: str = '',
                 exterior_color: str | BaseColor = '',
                 interior_color: str | BaseColor = '',
                 mileage: int = 0,
                 fuel_type: str | FuelType = '',
                 transmission: str | Transmission | None = None,
                 price: float = 0.0,
                 title: str = '',
                 description: str = '',
                 location: str = '',
                 groups: list[str] = None,
                 stockno: str = ''):
        self.photos_folder = photos_folder
        self.photos_names = photos_names
        self.vehicle_type = VehicleType.from_str(vehicle_type)
        self.vehicle_condition = None if vehicle_condition is None else VehicleCondition.from_str(vehicle_condition)
        self.body_type = BodyType.from_str(body_type)
        self.year = year
        self.make = make
        self.model = model
        self.exterior_color = BaseColor.from_str(exterior_color)
        self.interior_color = BaseColor.from_str(interior_color)
        self.mileage = mileage
        self.fuel_type = FuelType.from_str(fuel_type)
        self.transmission = None if transmission is None else Transmission.from_str(transmission)
        self.price = price
        self.title = title
        self.description = description
        self.location = location
        self.groups = groups
        self.stockno = stockno

        if not self.photos_folder and self.stockno:
            photos_folder_abs = os.path.join(Path(__file__).resolve().parent, CONFIG_PHOTOS_BASE_FOLDER)
            self.photos_folder = os.path.join(photos_folder_abs, self.stockno)


# def get_data_from_csv(csv_file_name: str):
def get_data_from_csv(file_path: str):
    data = []

    try:
        with open(file_path, encoding="utf-8") as csv_file:
            csv_dictionary = csv.DictReader(csv_file, delimiter=',')

            for dictionary_row in csv_dictionary:
                data.append(dictionary_row)
    except:
        print('File was not found in csvs' + file_path)
        exit()

    return data


def push_data_to_csv(rows: list[Row], file_path: str):
    headers = [
        Row.HEADER_PHOTOS_FOLDER,
        Row.HEADER_PHOTOS_NAMES,
        Row.HEADER_VEHICLE_TYPE,
        Row.HEADER_VEHICLE_CONDITION,
        Row.HEADER_YEAR,
        Row.HEADER_MAKE,
        Row.HEADER_MODEL,
        Row.HEADER_EXTERIOR_COLOR,
        Row.HEADER_INTERIOR_COLOR,
        Row.HEADER_MILEAGE,
        Row.HEADER_FUEL_TYPE,
        Row.HEADER_PRICE,
        Row.HEADER_DESCRIPTION,
        Row.HEADER_LOCATION,
        Row.HEADER_GROUPS
    ]

    with open(file_path, mode="w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)

        writer.writerow(headers)

        for row in rows:
            writer.writerow([
                row.photos_folder,
                '; '.join(row.photos_names),
                row.vehicle_type,
                row.vehicle_condition,
                row.year if row.year is not None else '',
                row.make,
                row.model,
                row.exterior_color,
                row.interior_color,
                row.mileage,
                row.fuel_type,
                row.price,
                row.description,
                row.location,
                '; '.join(row.groups)
            ])
