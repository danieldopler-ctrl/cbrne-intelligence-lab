from dataclasses import dataclass


@dataclass(frozen=True)
class GallonConversion:
    gallons: float
    approximate: bool
    source_unit: str


LIQUID_GALLON_FACTORS: dict[str, tuple[float, bool]] = {
    "LGA": (1.0, False),
    "GALLON(S)": (1.0, False),
    "BARREL(S)": (42.0, True),
    "QUART(S)": (0.25, False),
    "PINT(S)": (0.125, False),
    "CUP(S)": (0.0625, False),
    "TABLESPOON(S)": (0.00390625, True),
    "TEASPOON(S)": (0.0013020833, True),
    "LITER(S)": (0.2641720524, True),
    "MILLILITER(S)": (0.0002641721, True),
}


def to_gallons(quantity: float, unit: str | None) -> GallonConversion | None:
    normalized_unit = str(unit or "").strip().upper()
    factor_info = LIQUID_GALLON_FACTORS.get(normalized_unit)
    if not factor_info:
        return None
    factor, approximate = factor_info
    return GallonConversion(
        gallons=quantity * factor,
        approximate=approximate,
        source_unit=normalized_unit,
    )
