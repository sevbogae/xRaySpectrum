import xraylib
from dataclasses import dataclass


@dataclass
class Material:
    name: str
    formula: str
    density_gcm3: float


def get_linear_attenuation_coefficient(material: str, energy_kev: float, density_g_cm3: float) -> float:
    """Get the linear attenuation coefficient for a given material and energy.

    Parameters
    ----------
    material : str
        The material for which to calculate the attenuation coefficient (e.g., 'Al', 'Cu').
    energy_kev : float
        The energy (in keV) for which to calculate the attenuation coefficient.
    density_g_cm3 : float
        The density of the material in g/cm^3.

    Returns
    -------
    float
        The linear attenuation coefficient in cm^-1.
    """
    return xraylib.CS_Total_CP(material, energy_kev) * density_g_cm3


if __name__ == "__main__":
    materials: list[Material] = [
        # Catphan 440.
        Material(name="Air", formula="Air, Dry (near sea level)", density_gcm3=0.0),
        Material(name="teflon_catphan", formula="Polytetrafluoroethylene (Teflon)", density_gcm3=2.16),
        Material(name="acrylic_catphan", formula="Polymethyl Methacralate (Lucite, Perspex)", density_gcm3=1.18),
        Material(name="ldpe_catphan", formula="Polyethylene", density_gcm3=0.92),

        # Leeds mini.
        Material(name="pvc_minileeds", formula="Polyvinyl Chloride", density_gcm3=1.38),
        Material(name="pmma_minileeds", formula="Polymethyl Methacralate (Lucite, Perspex)", density_gcm3=1.20),

        # QUART DVTap.
        Material(name="pvc_quart", formula="Polyvinyl Chloride", density_gcm3=1.41),
        Material(name="pmma_quart", formula="Polymethyl Methacralate (Lucite, Perspex)", density_gcm3=1.19),

        # SedentexCT IQ (no direct source).
        Material(name="pmma_sedentex", formula="Polymethyl Methacralate (Lucite, Perspex)", density_gcm3=1.20),
        Material(name="ldpe_sedentex", formula="Polyethylene", density_gcm3=0.92),
        Material(name="delrin_sedentex", formula="CH2O", density_gcm3=1.41),
        Material(name="ptfe_sedentex", formula="Polytetrafluoroethylene (Teflon)", density_gcm3=2.20),
        Material(name="aluminium_sedentex", formula="Al", density_gcm3=2.699)
    ]
    print(xraylib.GetCompoundDataNISTList())
    # 'Polytetrafluoroethylene (Teflon)'
    # 'Air, Dry (near sea level)'
    # 'Polyethylene'
    # "Polymethyl Methacralate (Lucite, Perspex)"

    for material in materials:
        att = get_linear_attenuation_coefficient(material.formula, 60, material.density_gcm3)
        print(material.name, material.formula, material.density_gcm3, att)
