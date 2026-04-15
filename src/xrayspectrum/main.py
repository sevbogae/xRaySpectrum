import spekpy as sp

s = sp.Spek(kvp=110, th=12)        # 110 kVp, 12° anode angle
s.filter('Al', 6.0)                 # ~6 mm Al total filtration (estimate)

s.get_plot(show=True)               # visualise spectrum
print(f"Mean energy: {s.get_emean():.1f} keV")
print(f"HVL1 (Al): {s.get_hvl1():.2f} mm Al")