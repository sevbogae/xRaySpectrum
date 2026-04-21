from typing import Iterable, Literal

import numpy as np
import spekpy as sp

def generate_spectrum(tube_voltage: float, delta_kev = 0.5, anode_angle_deg: float = 12,
                      target: Literal["Cr", "Cu", "Mo", "Rh", "Ag", "W", "Au"] = "W",
                      filtration_mm: Iterable[tuple[str, float]] = ()) -> sp.Spek:
    """Generate an X-ray spectrum given tube voltage, anode angle, and filtration.

    Parameters
    ----------
    tube_voltage : float
        tube voltage.
    delta_kev : float = 0.5
        The keV step in the spectrum.
    anode_angle_deg : float
        The anode angle in degrees.
    target : Literal["Cr", "Cu", "Mo", "Rh", "Ag", "W", "Au"] = "W"
        The target material of the X-ray tube.
    filtration_mm : Iterable[tuple[str, float]]
        A list of tuples where each tuple contains the filter material (e.g., 'Al') and its thickness in mm (e.g., 6.0).

    Returns
    -------
    sp.Spek
        An X-ray spectrum as a Spek model.
    """
    spectrum = sp.Spek(kvp=tube_voltage, dk=delta_kev, th=anode_angle_deg, targ=target
                       ).multi_filter(list(filtration_mm))
    return spectrum


if __name__ == "__main__":
    # flu   | diff  | unit         | meaning
    # --------------------------------------------------------------------------------------------------
    # True  | True  | cm^-2 keV^-1 | spk_{flu=True,diff=True}: Fluence, differential in energy.
    # True  | False | cm^-2        | spk_{flu=True,diff=False}: Fluence, integrated over energy.
    # False | True  | cm^-2        | spk_{flu=False,diff=True}: Energy fluence, differential in energy.
    # False | False | cm^-2 keV    | spk_{flu=False,diff=False}: Energy fluence, integrated over energy.
    #
    # Relations
    # ---------
    # spk_{flu=True,diff=False} = spk_{flu=True,diff=True} x ΔE
    # spk_{flu=False,diff=True} = spk_{flu=True,diff=True} x E
    # spk_{flu=False,diff=False} = spk_{flu=True,diff=True} x E x ΔE
    e, i = generate_spectrum(120, filtration_mm=[("Al", 1.4+9.5)]).get_spectrum(flu=True, diff=True)
    print(np.average(e, weights=i))
    import matplotlib.pyplot as plt
    plt.plot(e, i)
    plt.show()
