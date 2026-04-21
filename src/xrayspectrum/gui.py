import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib.pyplot as plt
import spekpy as sp
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from xrayspectrum.spectrum import generate_spectrum

TARGET_MATERIALS = ["Cr", "Cu", "Mo", "Rh", "Ag", "W", "Au"]

_matl_dir = os.path.join(os.path.dirname(sp.__file__), "data", "matl_def")
FILTER_MATERIALS: list[str] = sorted(
    f[:-5] for f in os.listdir(_matl_dir) if f.endswith(".comp")
)

FILTRATION_INFO = (
    "Accepted material names (case-sensitive):\n"
    "  • Element symbols: Al, Cu, Fe, Pb, W, …\n"
    "  • Compound names: Water, Liquid  |  Polyethylene  |  Air  |  …\n\n"
    "Start typing to filter the dropdown list.\n"
    f"({len(FILTER_MATERIALS)} materials available)"
)


class Tooltip:
    """Show a floating tooltip when the mouse hovers over a widget."""

    _PAD = 6

    def __init__(self, widget: tk.Widget, text: str):
        self._widget = widget
        self._text = text
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event=None):
        if self._tip:
            return
        x = self._widget.winfo_rootx() + self._widget.winfo_width() + 4
        y = self._widget.winfo_rooty()
        self._tip = tk.Toplevel(self._widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            self._tip, text=self._text, justify="left",
            background="#fffbe6", relief="solid", borderwidth=1,
            font=("", 9), padx=self._PAD, pady=self._PAD,
        )
        lbl.pack()

    def _hide(self, _event=None):
        if self._tip:
            self._tip.destroy()
            self._tip = None


class AutocompleteEntry(ttk.Entry):
    """Entry with a suggestion popup that never steals focus."""

    def __init__(self, parent, all_values: list[str], **kwargs):
        self._all_values = all_values
        super().__init__(parent, **kwargs)
        self._popup: tk.Toplevel | None = None
        self._listbox: tk.Listbox | None = None
        self.bind("<KeyRelease>", self._on_key)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Escape>", lambda _e: self._close())
        self.bind("<Return>", self._confirm)
        self.bind("<Down>", self._move_down)
        self.bind("<Up>", self._move_up)

    def _on_key(self, event):
        if event.keysym in ("Down", "Up", "Return", "Escape", "Tab"):
            return
        typed = self.get()
        filtered = [v for v in self._all_values if v.lower().startswith(typed.lower())] if typed else self._all_values
        if filtered:
            self._show(filtered)
        else:
            self._close()

    def _show(self, values):
        if self._popup is None:
            self._popup = tk.Toplevel(self)
            self._popup.wm_overrideredirect(True)
            self._popup.wm_attributes("-topmost", True)
            sb = ttk.Scrollbar(self._popup, orient="vertical")
            self._listbox = tk.Listbox(
                self._popup, yscrollcommand=sb.set,
                exportselection=False, takefocus=False,
                activestyle="dotbox",
            )
            sb.config(command=self._listbox.yview)
            self._listbox.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            self._listbox.bind("<ButtonRelease-1>", self._on_click)

        self._listbox.delete(0, tk.END)
        for v in values:
            self._listbox.insert(tk.END, v)
        self._listbox.config(height=min(8, len(values)))

        self._popup.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        w = max(self.winfo_width(), self._popup.winfo_reqwidth())
        h = self._popup.winfo_reqheight()
        self._popup.geometry(f"{w}x{h}+{x}+{y}")
        self._popup.deiconify()

    def _close(self):
        if self._popup:
            self._popup.destroy()
            self._popup = None
            self._listbox = None

    def _on_focus_out(self, _event):
        self.after(100, lambda: self._close() if self.focus_get() is not self else None)

    def _on_click(self, _event):
        self._pick()

    def _confirm(self, _event):
        if self._popup:
            self._pick()
            return "break"

    def _pick(self):
        if self._listbox:
            sel = self._listbox.curselection()
            if sel:
                self.delete(0, tk.END)
                self.insert(0, self._listbox.get(sel[0]))
        self._close()
        self.focus_set()

    def _move_down(self, _event):
        if self._listbox:
            sel = self._listbox.curselection()
            idx = (sel[0] + 1) if sel else 0
            idx = min(idx, self._listbox.size() - 1)
            self._listbox.selection_clear(0, tk.END)
            self._listbox.selection_set(idx)
            self._listbox.see(idx)
        return "break"

    def _move_up(self, _event):
        if self._listbox and (sel := self._listbox.curselection()):
            idx = max(sel[0] - 1, 0)
            self._listbox.selection_clear(0, tk.END)
            self._listbox.selection_set(idx)
            self._listbox.see(idx)
        return "break"


class FiltrationRow:
    def __init__(self, parent_frame: ttk.Frame, on_remove):
        self.frame = ttk.Frame(parent_frame)
        self.frame.pack(fill="x", pady=2)

        ttk.Label(self.frame, text="Material:", width=9, anchor="w").pack(side="left")
        self.material_var = tk.StringVar()
        AutocompleteEntry(
            self.frame, all_values=FILTER_MATERIALS,
            textvariable=self.material_var, width=32,
        ).pack(side="left", padx=(0, 8))

        ttk.Label(self.frame, text="Thickness (mm):", anchor="w").pack(side="left")
        self.thickness_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.thickness_var, width=8).pack(side="left", padx=(0, 8))

        ttk.Button(self.frame, text="✕", width=2, command=lambda: on_remove(self)).pack(side="left")

    def get(self) -> tuple[str, float] | None:
        mat = self.material_var.get().strip()
        thick = self.thickness_var.get().strip()
        if (not mat) and (not thick):
            return None
        if (not mat) or (not thick):
            raise ValueError(f"Incomplete filtration entry: material='{mat}', thickness='{thick}'")
        return mat, float(thick)

    def destroy(self):
        self.frame.destroy()


class XRaySpectrumApp(tk.Tk):
    """A graphical user interface for X-ray spectrum generation with SpekPy."""

    def __init__(self):
        super().__init__()
        self.title("X-Ray Spectrum Generator")
        self.resizable(True, True)
        _ico = os.path.join(os.path.dirname(__file__), "spectrum_generator.ico")
        if os.path.exists(_ico):
            self.iconbitmap(_ico)

        self._filtration_rows: list[FiltrationRow] = []
        self._spectrum_data: tuple[np.ndarray, np.ndarray] | None = None

        # self._setup_styles()
        self._build_ui()
        # Set the minimum size once the window has been laid out
        self.after(50, self._apply_min_size)

    def _apply_min_size(self):
        self.update_idletasks()
        self.minsize(self.winfo_width(), self.winfo_height())

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Accent.TButton",
            font=("", 10, "bold"),
            foreground="white",
            background="#2563eb",
            bordercolor="#1d4ed8",
            focuscolor="#1d4ed8",
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#1d4ed8"), ("pressed", "#1e40af")],
            foreground=[("active", "white")],
        )

    def _build_ui(self):
        """Build the user interface."""
        main_frame = ttk.Frame(self, padding=12)
        main_frame.pack(fill="both", expand=True)

        # ── Tube parameters ──────────────────────────────────────────────
        params_label_frame = ttk.LabelFrame(main_frame, text="Tube Parameters", padding=8)
        params_label_frame.pack(fill="x", pady=(0, 8))

        params_frame = ttk.Frame(params_label_frame)
        params_frame.pack(fill="x")

        ttk.Label(params_frame, text="Tube voltage (kV):", width=20, anchor="w").grid(row=0, column=0, sticky="w")
        self._kvp_var = tk.StringVar(value="120")
        ttk.Entry(params_frame, textvariable=self._kvp_var, width=10).grid(row=0, column=1, sticky="w", padx=(0, 20))

        ttk.Label(params_frame, text="Anode angle (°):", width=16, anchor="w").grid(row=0, column=2, sticky="w")
        self._angle_var = tk.StringVar(value="12")
        ttk.Entry(params_frame, textvariable=self._angle_var, width=10).grid(row=0, column=3, sticky="w", padx=(0, 20))

        ttk.Label(params_frame, text="Target material:", width=16, anchor="w").grid(row=0, column=4, sticky="w")
        self._target_var = tk.StringVar(value="W")
        ttk.Combobox(
            params_frame, textvariable=self._target_var,
            values=TARGET_MATERIALS, state="readonly", width=6,
        ).grid(row=0, column=5, sticky="w")

        # ── Filtration ────────────────────────────────────────────────────
        filt_lf = ttk.LabelFrame(main_frame, text="Filtration", padding=8)
        filt_lf.pack(fill="x", pady=(0, 8))

        self._filt_container = ttk.Frame(filt_lf)
        self._filt_container.pack(fill="x")

        filt_btn_row = ttk.Frame(filt_lf)
        filt_btn_row.pack(anchor="w", pady=(6, 0))
        ttk.Button(filt_btn_row, text="+ Add filtration layer", command=self._add_filtration).pack(side="left")
        info_btn = ttk.Button(filt_btn_row, text="ℹ", width=2)
        info_btn.pack(side="left", padx=(6, 0))
        Tooltip(info_btn, FILTRATION_INFO)

        # ── Generate button ───────────────────────────────────────────────
        ttk.Button(
            main_frame, text="Generate Spectrum",
            style="Accent.TButton",
            command=self._generate,
        ).pack(pady=(4, 8), ipadx=10, ipady=4)

        # ── Plot ──────────────────────────────────────────────────────────
        plot_lf = ttk.LabelFrame(main_frame, text="Spectrum", padding=8)
        plot_lf.pack(fill="both", expand=True, pady=(0, 8))

        self._fig, self._ax = plt.subplots(figsize=(7, 3.5), tight_layout=True)
        self._ax.set_xlabel("Energy (keV)")
        self._ax.set_ylabel("Fluence per mAs (photons/cm²/mAs/keV)")
        self._ax.set_title("X-Ray Spectrum")
        self._canvas = FigureCanvasTkAgg(self._fig, master=plot_lf)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        # ── Export ────────────────────────────────────────────────────────
        export_lf = ttk.LabelFrame(main_frame, text="Export", padding=8)
        export_lf.pack(fill="x")

        export_row = ttk.Frame(export_lf)
        export_row.pack(fill="x")

        ttk.Label(export_row, text="kev step for export:", anchor="w").pack(side="left")
        self._kv_step_var = tk.StringVar(value="1")
        ttk.Entry(export_row, textvariable=self._kv_step_var, width=8).pack(side="left", padx=(4, 16))

        ttk.Button(export_row, text="Export to .txt", command=self._export).pack(side="left", ipadx=6, ipady=2)

    def _add_filtration(self):
        row = FiltrationRow(self._filt_container, self._remove_filtration)
        self._filtration_rows.append(row)

    def _remove_filtration(self, row: FiltrationRow):
        self._filtration_rows.remove(row)
        row.destroy()

    def _parse_inputs(self) -> tuple[float, float, str, list[tuple[str, float]]]:
        kvp = float(self._kvp_var.get())
        angle = float(self._angle_var.get())
        target = self._target_var.get()

        filtration: list[tuple[str, float]] = []
        for frow in self._filtration_rows:
            result = frow.get()
            if result is not None:
                filtration.append(result)

        return kvp, angle, target, filtration

    def _generate(self):
        try:
            kvp, angle, target, filtration = self._parse_inputs()
        except ValueError as exc:
            messagebox.showerror("Input error", str(exc))
            return

        try:
            spectrum: sp.Spek = generate_spectrum(
                tube_voltage=kvp,
                anode_angle_deg=angle,
                target=target,
                filtration_mm=filtration,
                delta_kev=0.5,
            )
            energies, intensities = spectrum.get_spectrum(flu=True, diff=True)
        except Exception as exc:
            messagebox.showerror("Spectrum error", str(exc))
            return

        self._spectrum_data = energies, intensities

        self._ax.cla()
        self._ax.plot(energies, intensities, color="#2563eb", linewidth=1.2)
        self._ax.set_xlabel("Energy (keV)")
        self._ax.set_ylabel("Fluence per mAs (photons/cm²/mAs/keV)")
        filt_str = ", ".join(f"{m} {t} mm" for m, t in filtration) if filtration else "none"
        self._ax.set_title(f"{kvp} kVp  |  {target}  |  {angle}°  |  filtration: {filt_str}")
        self._ax.set_xlim(left=0)
        self._ax.set_ylim(bottom=0)
        self._canvas.draw()

    def _export(self):
        if self._spectrum_data is None:
            messagebox.showwarning("No spectrum", "Generate a spectrum first.")
            return

        try:
            kv_step = float(self._kv_step_var.get())
            if kv_step < 0.5:
                raise ValueError("kev step must be at least 0.5 keV.")
        except ValueError as exc:
            messagebox.showerror("Input error", str(exc))
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile="spectrum.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save spectrum",
        )
        if not path:
            return

        energies, intensities = self._spectrum_data
        try:
            kvp, angle, target, filtration = self._parse_inputs()
        except ValueError:
            kvp, angle, target, filtration = None, None, None, []

        # Resample to requested kV step via interpolation
        e_min = energies[0]
        e_max = energies[-1]
        export_energies = np.arange(e_min, e_max + kv_step / 2, kv_step)
        export_intensities = np.interp(export_energies, energies, intensities)

        with open(path, "w", encoding="utf-8") as f:
            f.write("# X-Ray Spectrum Export\n")
            if kvp is not None:
                filt_str = ", ".join(f"{m} {t} mm" for m, t in filtration) if filtration else "none"
                f.write(f"# KVp={kvp}  Anode angle={angle} deg  Target={target}  Filtration={filt_str}\n")
            f.write(f"# kV step = {kv_step} keV\n")
            f.write("# Energy (keV)\tFluence per mAs (photons/cm2/mAs/keV)\n")
            for e, i in zip(export_energies, export_intensities):
                f.write(f"{e:.4f}\t{i:.6e}\n")

        messagebox.showinfo("Exported", f"Spectrum saved to:\n{path}")


def main():
    app = XRaySpectrumApp()
    app.mainloop()


if __name__ == "__main__":
    main()
