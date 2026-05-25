from __future__ import annotations

from dataclasses import dataclass


EPA_RMP_TOXIC_REFERENCE_URL = (
    "https://www.ecfr.gov/current/title-40/chapter-I/subchapter-C/part-68/section-68.130"
)

# 40 CFR 68.130 Table 1, alphabetical list of 77 regulated toxic substances.
EPA_RMP_TOXIC_SUBSTANCES = frozenset(
    {
        "acrolein",
        "acrylonitrile",
        "acrylyl chloride",
        "allyl alcohol",
        "allylamine",
        "ammonia (anhydrous)",
        "ammonia (conc 20% or greater)",
        "arsenous trichloride",
        "arsine",
        "boron trichloride",
        "boron trifluoride",
        "boron trifluoride compound with methyl ether (1:1)",
        "bromine",
        "carbon disulfide",
        "chlorine",
        "chlorine dioxide",
        "chloroform",
        "chloromethyl ether",
        "chloromethyl methyl ether",
        "crotonaldehyde",
        "crotonaldehyde, (e)-",
        "cyanogen chloride",
        "cyclohexylamine",
        "diborane",
        "dimethyldichlorosilane",
        "1,1-dimethylhydrazine",
        "epichlorohydrin",
        "ethylenediamine",
        "ethyleneimine",
        "ethylene oxide",
        "fluorine",
        "formaldehyde (solution)",
        "furan",
        "hydrazine",
        "hydrochloric acid (conc 37% or greater)",
        "hydrocyanic acid",
        "hydrogen chloride (anhydrous)",
        "hydrogen fluoride/hydrofluoric acid (conc 50% or greater)",
        "hydrogen selenide",
        "hydrogen sulfide",
        "iron, pentacarbonyl-",
        "isobutyronitrile",
        "isopropyl chloroformate",
        "methacrylonitrile",
        "methyl chloride",
        "methyl chloroformate",
        "methyl hydrazine",
        "methyl isocyanate",
        "methyl mercaptan",
        "methyl thiocyanate",
        "methyltrichlorosilane",
        "nickel carbonyl",
        "nitric acid (conc 80% or greater)",
        "nitric oxide",
        "oleum (fuming sulfuric acid)",
        "peracetic acid",
        "perchloromethylmercaptan",
        "phosgene",
        "phosphine",
        "phosphorus oxychloride",
        "phosphorus trichloride",
        "piperidine",
        "propionitrile",
        "propyl chloroformate",
        "propyleneimine",
        "propylene oxide",
        "sulfur dioxide (anhydrous)",
        "sulfur tetrafluoride",
        "sulfur trioxide",
        "tetramethyllead",
        "tetranitromethane",
        "titanium tetrachloride",
        "toluene 2,4-diisocyanate",
        "toluene 2,6-diisocyanate",
        "toluene diisocyanate (unspecified isomer)",
        "trimethylchlorosilane",
        "vinyl acetate monomer",
    }
)

# These aliases preserve an unambiguous match to a Table 1 name.
EPA_RMP_TOXIC_ALIASES = {
    "chlorine gas": "chlorine",
    "anhydrous ammonia": "ammonia (anhydrous)",
}


@dataclass(frozen=True)
class ToxicSubstanceMatch:
    source_commodity: str
    regulated_substance: str
    match_method: str


def match_rmp_toxic_substance(commodity: str | None) -> ToxicSubstanceMatch | None:
    if not commodity:
        return None
    normalized = " ".join(commodity.casefold().split())
    if normalized in EPA_RMP_TOXIC_SUBSTANCES:
        return ToxicSubstanceMatch(commodity, normalized, "normalized_exact")
    regulated_substance = EPA_RMP_TOXIC_ALIASES.get(normalized)
    if regulated_substance:
        return ToxicSubstanceMatch(commodity, regulated_substance, "curated_alias")
    return None
