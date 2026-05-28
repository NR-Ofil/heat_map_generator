"""
Shared OverlayGUI widget — interactive heatmap overlay with adjustable parameters.
Used by both heatmap_app.py and heatmap_viewer.py.
"""

import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from PIL import Image, ImageTk
import config


class OverlayGUI:
    """Interactive overlay GUI for a single processed video."""

    def __init__(self, root, matrix_file, frame_file, output_folder):
        self.root = root
        self.root.title("Red-Spot Heatmap Overlay - Interactive")
        self.output_folder = Path(output_folder)

        self.cumulative_matrix = np.load(str(matrix_file))
        self.representative_frame = np.load(str(frame_file))

        self.min_threshold = tk.DoubleVar(value=0.0)
        self.max_threshold = tk.DoubleVar(value=float(self.cumulative_matrix.max()))
        self.alpha = tk.DoubleVar(value=0.55)
        self.dynamic_range_min = tk.DoubleVar(value=0.0)
        self.dynamic_range_max = tk.DoubleVar(value=100.0)

        self.current_overlay = None

        self._create_widgets()
        self.update_overlay()

    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        image_frame = ttk.Frame(main_frame)
        image_frame.grid(row=0, column=0, columnspan=2, pady=10)
        self.image_label = ttk.Label(image_frame)
        self.image_label.pack()

        controls_frame = ttk.LabelFrame(main_frame, text="Parameters", padding="10")
        controls_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        matrix_max = float(self.cumulative_matrix.max())

        rows = [
            ("Min Threshold:",          self.min_threshold,      0.0,   matrix_max, self._fmt2),
            ("Max Threshold:",          self.max_threshold,      0.0,   matrix_max, self._fmt2),
            ("Alpha (Overlay):",        self.alpha,              0.0,   1.0,        self._fmt2),
            ("Dynamic Range Min (%):",  self.dynamic_range_min,  0.0,   100.0,      self._fmt1pct),
            ("Dynamic Range Max (%):",  self.dynamic_range_max,  0.0,   100.0,      self._fmt1pct),
        ]

        self._value_labels = []
        for i, (label_text, var, from_, to, fmt) in enumerate(rows):
            ttk.Label(controls_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=5)
            ttk.Scale(
                controls_frame, from_=from_, to=to, variable=var,
                orient=tk.HORIZONTAL, length=300,
                command=lambda v: self.update_overlay()
            ).grid(row=i, column=1, sticky=(tk.W, tk.E), padx=5)
            lbl = ttk.Label(controls_frame, text=fmt(var.get()))
            lbl.grid(row=i, column=2, padx=5)
            var.trace('w', lambda *a, v=var, l=lbl, f=fmt: l.config(text=f(v.get())))
            self._value_labels.append(lbl)

        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(buttons_frame, text="Save Overlay", command=self.save_overlay).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Reset", command=self.reset_parameters).pack(side=tk.LEFT, padx=5)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(1, weight=1)

    @staticmethod
    def _fmt2(v): return f"{float(v):.2f}"
    @staticmethod
    def _fmt1pct(v): return f"{float(v):.1f}%"

    def _apply_dynamic_range(self, matrix):
        min_val = np.percentile(matrix, self.dynamic_range_min.get())
        max_val = np.percentile(matrix, self.dynamic_range_max.get())
        clipped = np.clip(matrix, min_val, max_val)
        if max_val > min_val:
            normalized = (clipped - min_val) / (max_val - min_val)
        else:
            normalized = np.zeros_like(clipped)
        return normalized * 255.0

    def update_overlay(self):
        matrix = self.cumulative_matrix.copy()
        min_thresh = self.min_threshold.get()
        max_thresh = self.max_threshold.get()

        mask = (matrix >= min_thresh).astype(np.uint8)
        matrix = np.clip(matrix, min_thresh, max_thresh)
        matrix_u8 = self._apply_dynamic_range(matrix).astype(np.uint8)

        colormap_map = {
            "JET": cv2.COLORMAP_JET, "HOT": cv2.COLORMAP_HOT,
            "PLASMA": cv2.COLORMAP_PLASMA, "VIRIDIS": cv2.COLORMAP_VIRIDIS,
        }
        colormap = colormap_map.get(config.COLORMAP.upper(), cv2.COLORMAP_JET)
        heatmap_bgr = cv2.applyColorMap(matrix_u8, colormap)

        base = self.representative_frame.copy()
        alpha_val = self.alpha.get()
        blended = cv2.addWeighted(base, 1.0 - alpha_val, heatmap_bgr, alpha_val, 0.0)

        mask_3d = mask[:, :, np.newaxis]
        overlay_bgr = base * (1 - mask_3d) + blended * mask_3d

        overlay_rgb = cv2.cvtColor(overlay_bgr, cv2.COLOR_BGR2RGB)

        display_size = 800
        h, w = overlay_rgb.shape[:2]
        if w > display_size or h > display_size:
            scale = display_size / max(w, h)
            overlay_rgb = cv2.resize(overlay_rgb, (int(w * scale), int(h * scale)))

        photo = ImageTk.PhotoImage(image=Image.fromarray(overlay_rgb))
        self.image_label.config(image=photo)
        self.image_label.image = photo

        self.current_overlay = overlay_bgr

    def save_overlay(self):
        params = (
            f"min{self.min_threshold.get():.1f}"
            f"_max{self.max_threshold.get():.1f}"
            f"_alpha{self.alpha.get():.2f}"
            f"_dr{self.dynamic_range_min.get():.0f}-{self.dynamic_range_max.get():.0f}"
        )
        output_file = self.output_folder / f"overlay_{params}.png"
        cv2.imwrite(str(output_file), self.current_overlay)
        messagebox.showinfo("Saved", f"Overlay saved to:\n{output_file}")

    def reset_parameters(self):
        self.min_threshold.set(0.0)
        self.max_threshold.set(float(self.cumulative_matrix.max()))
        self.alpha.set(0.55)
        self.dynamic_range_min.set(0.0)
        self.dynamic_range_max.set(100.0)
        self.update_overlay()
