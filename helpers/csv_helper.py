import csv
import dataclasses
from dataclasses import asdict
from enum import StrEnum, Enum


class BaseEnum(StrEnum):
    @classmethod
    def from_str(cls, value: str):
        if not value:
            return getattr(cls, "_default_value", None)
        for item in cls:
            if item.value.lower() == value.lower():
                return item
        return getattr(cls, "_default_value", None)


class VehicleType(BaseEnum):
    CAR_TRUCK = 'Car/Track'
    MOTORCYCLE = 'Motorcycle'
    POWERSPORT = 'Powersport'
    RV_CAMPER = 'RV/Camper'
    TRAILER = 'Trailer'
    BOAT = 'Boat'
    COMMERCIAL_INDUSTRIAL = 'Commercial/Industrial'
    OTHER = 'Other'

    _default_value = CAR_TRUCK


class BodyType(BaseEnum):
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

    _default_value = OTHER


class BaseColor(BaseEnum):
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

    _default_value = OTHER


class FuelType(BaseEnum):
    DIESEL = "Diesel"
    ELECTRIC = "Electric"
    GASOLINE = "Gasoline"
    FLEX = "Flex"
    HYBRID = "Hybrid"
    PETROL = "Petrol"
    PLUG_IN_HYBRID = "Plug-in hybrid"
    OTHER = "Other"

    _default_value = OTHER


class VehicleCondition(BaseEnum):
    EXCELLENT = "Excellent"
    VERY_GOOD = "Very good"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"

    _default_value = GOOD


class Transmission(BaseEnum):
    MANUAL = "Manual transmission"
    AUTOMATIC = "Automatic transmission"

    @classmethod
    def from_str(cls, value: str):
        result = super().from_str(value)
        if result:
            return result
        if value.lower() == 'manual':
            return Transmission.MANUAL
        if value.lower() == 'automatic':
            return Transmission.AUTOMATIC
        return result


@dataclasses.dataclass
class Row:
    photos_folder: str = ''
    photos_names: list[str] = None
    vehicle_type: VehicleType = VehicleType._default_value
    vehicle_condition: VehicleCondition | None = VehicleCondition._default_value
    body_type: BodyType = BodyType._default_value
    year: int | None = None
    make: str = ''
    model: str = ''
    exterior_color: BaseColor = BaseColor._default_value
    interior_color: BaseColor = BaseColor._default_value
    mileage: int = 0
    fuel_type: FuelType = FuelType._default_value
    transmission: Transmission | None = None
    price: float = 0.0
    title: str = ''
    description: str = ''
    location: str = ''
    groups: list[str] = None
    stockno: str = ''
    vin: str = ''

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)


def get_data_from_csv(file_path: str) -> list[Row]:
    rows = []
    with open(file_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row_dict in reader:
            rows.append(Row(
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
                price=row_dict.get('price', ''),
                title=row_dict.get('title', ''),
                description=row_dict.get('description', ''),
                location=row_dict.get('location', ''),
                groups=row_dict.get('groups', '').split(";"),
                stockno=row_dict.get('stockno', ''),
                vin=row_dict.get('vin', '')
            ))
    return rows


def push_data_to_csv(rows: list[Row], file_path: str):
    if not rows:
        return

    fieldnames = [f.name for f in dataclasses.fields(rows[0])]

    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            data = asdict(row)
            for key, value in data.items():
                if isinstance(value, Enum):
                    data[key] = value.value
                elif isinstance(value, list):
                    data[key] = ";".join(value)
            writer.writerow(data)
