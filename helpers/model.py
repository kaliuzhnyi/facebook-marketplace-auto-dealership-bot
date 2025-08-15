import dataclasses
import datetime
from enum import StrEnum


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
    CAR_TRUCK = 'Car/Truck'
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

    @classmethod
    def from_str(cls, value: str):
        result = super().from_str(value)
        if result and result != FuelType._default_value:
            return result
        if value.lower() == 'gas':
            return FuelType.GASOLINE
        return FuelType._default_value


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
        if 'automatic' in value.lower():
            return Transmission.AUTOMATIC
        return result


@dataclasses.dataclass
class Listing:
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


@dataclasses.dataclass
class PublishedListing:
    title: str = ''
    description: str = ''
    price: float = 0.0
    location: str = ''
    mileage: int = 0
    fuel_type: FuelType = None

    published_date: datetime.date = None


    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)