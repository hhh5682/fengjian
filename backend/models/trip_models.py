from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class Coordinates:
    lat: Optional[float] = None
    lng: Optional[float] = None

    def to_dict(self) -> Dict[str, Optional[float]]:
        return asdict(self)


@dataclass
class PlaceRef:
    name: str
    address: str = ""
    city: str = ""
    district: str = ""
    coords: Coordinates = field(default_factory=Coordinates)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["coords"] = self.coords.to_dict()
        return data


@dataclass
class TripRequest:
    departure: str
    destination: str
    departure_time: str
    return_time: str
    departure_coords: Coordinates = field(default_factory=Coordinates)
    destination_coords: Coordinates = field(default_factory=Coordinates)
    transport_modes: List[str] = field(default_factory=lambda: ["高铁", "飞机", "大巴", "顺风车"])
    hotel_anchor: Optional[str] = None
    hotel_anchor_coords: Coordinates = field(default_factory=Coordinates)
    interests: List[str] = field(default_factory=list)
    food_preferences: List[str] = field(default_factory=list)
    budget: Optional[float] = None
    adults: int = 1

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TripRequest":
        departure_coords = cls._normalize_coords(data.get("departureCoords"))
        destination_coords = cls._normalize_coords(data.get("destinationCoords"))
        hotel_anchor_coords = cls._normalize_coords(data.get("hotelAnchorCoords"))

        return cls(
            departure=data.get("departure", ""),
            destination=data.get("destination", ""),
            departure_time=data.get("departureTime", ""),
            return_time=data.get("returnTime", ""),
            departure_coords=departure_coords,
            destination_coords=destination_coords,
            transport_modes=data.get("transportModes") or ["高铁", "飞机", "大巴", "顺风车"],
            hotel_anchor=data.get("hotelAnchor"),
            hotel_anchor_coords=hotel_anchor_coords,
            interests=data.get("interests") or [],
            food_preferences=data.get("foodPreferences") or [],
            budget=data.get("budget"),
            adults=int(data.get("adults") or 1),
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["departure_coords"] = self.departure_coords.to_dict()
        data["destination_coords"] = self.destination_coords.to_dict()
        data["hotel_anchor_coords"] = self.hotel_anchor_coords.to_dict()
        return data

    @staticmethod
    def _normalize_coords(value: Any) -> Coordinates:
        if isinstance(value, Coordinates):
            return value
        if isinstance(value, dict):
            return Coordinates(
                lat=value.get("lat"),
                lng=value.get("lng"),
            )
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            return Coordinates(
                lat=value[1],
                lng=value[0],
            )
        return Coordinates()


@dataclass
class TransportOption:
    transport_type: str
    trip_number: str
    departure_station: str
    arrival_station: str
    departure_time: str
    arrival_time: str
    duration: str
    estimated_price: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TransportPlan:
    label: str
    options: List[TransportOption] = field(default_factory=list)
    selected_index: int = 0

    @property
    def selected_option(self) -> Optional[TransportOption]:
        if 0 <= self.selected_index < len(self.options):
            return self.options[self.selected_index]
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "options": [item.to_dict() for item in self.options],
            "selectedIndex": self.selected_index,
            "selectedOption": self.selected_option.to_dict() if self.selected_option else None,
        }


@dataclass
class AttractionItem:
    play_time: str
    location: str
    opening_hours: str
    estimated_price_text: str
    day_label: str = ""
    period_label: str = ""
    start_time: str = ""
    end_time: str = ""
    estimated_price_value: float = 0.0
    coords: Coordinates = field(default_factory=Coordinates)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["coords"] = self.coords.to_dict()
        return data


@dataclass
class RestaurantOption:
    name: str
    estimated_price: float
    coords: Coordinates = field(default_factory=Coordinates)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["coords"] = self.coords.to_dict()
        return data


@dataclass
class MealItem:
    meal_time: str
    nearby_attraction: str
    meal_type: str
    day_label: str = ""
    period_label: str = ""
    meal_clock: str = ""
    options: List[RestaurantOption] = field(default_factory=list)
    selected_index: int = 0

    @property
    def selected_option(self) -> Optional[RestaurantOption]:
        if 0 <= self.selected_index < len(self.options):
            return self.options[self.selected_index]
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meal_time": self.meal_time,
            "nearby_attraction": self.nearby_attraction,
            "meal_type": self.meal_type,
            "day_label": self.day_label,
            "period_label": self.period_label,
            "meal_clock": self.meal_clock,
            "options": [item.to_dict() for item in self.options],
            "selectedIndex": self.selected_index,
            "selectedOption": self.selected_option.to_dict() if self.selected_option else None,
        }


@dataclass
class HotelOption:
    hotel_name: str
    nearby_landmark: str
    estimated_price: float
    coords: Coordinates = field(default_factory=Coordinates)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["coords"] = self.coords.to_dict()
        return data


@dataclass
class HotelPlan:
    options: List[HotelOption] = field(default_factory=list)
    selected_index: int = 0

    @property
    def selected_option(self) -> Optional[HotelOption]:
        if 0 <= self.selected_index < len(self.options):
            return self.options[self.selected_index]
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "options": [item.to_dict() for item in self.options],
            "selectedIndex": self.selected_index,
            "selectedOption": self.selected_option.to_dict() if self.selected_option else None,
        }


@dataclass
class StructuredTripPlan:
    transport: Dict[str, TransportPlan] = field(default_factory=dict)
    attractions: List[AttractionItem] = field(default_factory=list)
    foods: List[MealItem] = field(default_factory=list)
    hotels: HotelPlan = field(default_factory=HotelPlan)
    local_transports: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        transport_dict = {}
        if isinstance(self.transport, dict):
            for key, value in self.transport.items():
                if hasattr(value, 'to_dict'):
                    transport_dict[key] = value.to_dict()
                else:
                    transport_dict[key] = value
        
        return {
            "transport": transport_dict,
            "attractions": [item.to_dict() for item in self.attractions],
            "foods": [item.to_dict() for item in self.foods],
            "hotels": self.hotels.to_dict() if hasattr(self.hotels, 'to_dict') else self.hotels,
            "local_transports": self.local_transports,
        }


@dataclass
class AgentOption:
    id: str
    type: str
    title: str
    subtitle: str = ""
    price: float = 0.0
    currency: str = "CNY"
    score: float = 0.0
    source: str = ""
    tags: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineBlock:
    id: str
    day: int
    block_type: str
    title: str
    subtitle: str = ""
    start_time: str = ""
    end_time: str = ""
    price: float = 0.0
    location: str = ""
    card_type: str = ""
    selected: bool = False
    alternatives: List[str] = field(default_factory=list)
    fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PriceSummary:
    transport: float = 0.0
    hotel: float = 0.0
    attraction: float = 0.0
    food: float = 0.0

    @property
    def total(self) -> float:
        return self.transport + self.hotel + self.attraction + self.food

    def to_dict(self) -> Dict[str, float]:
        return {
            "transport": round(self.transport, 2),
            "hotel": round(self.hotel, 2),
            "attraction": round(self.attraction, 2),
            "food": round(self.food, 2),
            "total": round(self.total, 2),
        }


@dataclass
class LocalTransportRoute:
    from_location: Dict[str, Any]
    to_location: Dict[str, Any]
    routes: List[Dict[str, Any]] = field(default_factory=list)
    selected_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlannerResult:
    trip: Dict[str, Any]
    transport_hub: Dict[str, Any]
    attractions: List[Dict[str, Any]]
    hotels: List[Dict[str, Any]]
    foods: List[Dict[str, Any]]
    cards: Dict[str, List[Dict[str, Any]]]
    timeline: List[Dict[str, Any]]
    pricing: Dict[str, float]
    warnings: List[str] = field(default_factory=list)
    structured_plan: Dict[str, Any] = field(default_factory=dict)
    local_transports: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)