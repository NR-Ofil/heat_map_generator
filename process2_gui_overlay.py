"""
Process 2: Interactive GUI for creating overlay with adjustable parameters.
Allows user to adjust min/max threshold, alpha, and dynamic range.
"""

import cv2
import numpy as np
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
from PIL import Image, ImageTk
import config


class OverlayGUI:
    def __init__(self, root, matrix_file, frame_file):
        self.root = root
        self.root.title("Red-Spot Heatmap Overlay - Interactive")
        
        # Load data
        print(f"Loading cumulative matrix from: {matrix_file}")
        self.cumulative_matrix = np.load(str(matrix_file))
        print(f"Loading representative frame from: {frame_file}")
        self.representative_frame = np.load(str(frame_file))
        
        print(f"Matrix shape: {self.cumulative_matrix.shape}")
        print(f"Frame shape: {self.representative_frame.shape}")
        
        # Initialize parameters
        self.min_threshold = tk.DoubleVar(value=0.0)
        self.max_threshold = tk.DoubleVar(value=float(self.cumulative_matrix.max()))
        self.alpha = tk.DoubleVar(value=0.55)
        self.dynamic_range_min = tk.DoubleVar(value=0.0)
        self.dynamic_range_max = tk.DoubleVar(value=100.0)
        
        # Initialize overlay storage
        self.current_overlay = None
        
        # Create GUI
        self.create_widgets()
        
        # Initial render
        self.update_overlay()
    
    def create_widgets(self):
        """Create GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Image display frame
        image_frame = ttk.Frame(main_frame)
        image_frame.grid(row=0, column=0, columnspan=2, pady=10)
        
        self.image_label = ttk.Label(image_frame)
        self.image_label.pack()
        
        # Controls frame
        controls_frame = ttk.LabelFrame(main_frame, text="Parameters", padding="10")
        controls_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Min Threshold
        ttk.Label(controls_frame, text="Min Threshold:").grid(row=0, column=0, sticky=tk.W, pady=5)
        min_scale = ttk.Scale(
            controls_frame,
            from_=0.0,
            to=float(self.cumulative_matrix.max()),
            variable=self.min_threshold,
            orient=tk.HORIZONTAL,
            length=300,
            command=lambda v: self.update_overlay()
        )
        min_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.min_label = ttk.Label(controls_frame, text="0.00")
        self.min_label.grid(row=0, column=2, padx=5)
        self.min_threshold.trace('w', lambda *args: self.min_label.config(text=f"{self.min_threshold.get():.2f}"))
        
        # Max Threshold
        ttk.Label(controls_frame, text="Max Threshold:").grid(row=1, column=0, sticky=tk.W, pady=5)
        max_scale = ttk.Scale(
            controls_frame,
            from_=0.0,
            to=float(self.cumulative_matrix.max()),
            variable=self.max_threshold,
            orient=tk.HORIZONTAL,
            length=300,
            command=lambda v: self.update_overlay()
        )
        max_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        self.max_label = ttk.Label(controls_frame, text=f"{self.cumulative_matrix.max():.2f}")
        self.max_label.grid(row=1, column=2, padx=5)
        self.max_threshold.trace('w', lambda *args: self.max_label.config(text=f"{self.max_threshold.get():.2f}"))
        
        # Alpha (transparency)
        ttk.Label(controls_frame, text="Alpha (Overlay):").grid(row=2, column=0, sticky=tk.W, pady=5)
        alpha_scale = ttk.Scale(
            controls_frame,
            from_=0.0,
            to=1.0,
            variable=self.alpha,
            orient=tk.HORIZONTAL,
            length=300,
            command=lambda v: self.update_overlay()
        )
        alpha_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        self.alpha_label = ttk.Label(controls_frame, text="0.55")
        self.alpha_label.grid(row=2, column=2, padx=5)
        self.alpha.trace('w', lambda *args: self.alpha_label.config(text=f"{self.alpha.get():.2f}"))
        
        # Dynamic Range Min (%)
        ttk.Label(controls_frame, text="Dynamic Range Min (%):").grid(row=3, column=0, sticky=tk.W, pady=5)
        dr_min_scale = ttk.Scale(
            controls_frame,
            from_=0.0,
            to=100.0,
            variable=self.dynamic_range_min,
            orient=tk.HORIZONTAL,
            length=300,
            command=lambda v: self.update_overlay()
        )
        dr_min_scale.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        self.dr_min_label = ttk.Label(controls_frame, text="0.00")
        self.dr_min_label.grid(row=3, column=2, padx=5)
        self.dynamic_range_min.trace('w', lambda *args: self.dr_min_label.config(text=f"{self.dynamic_range_min.get():.1f}%"))
        
        # Dynamic Range Max (%)
        ttk.Label(controls_frame, text="Dynamic Range Max (%):").grid(row=4, column=0, sticky=tk.W, pady=5)
        dr_max_scale = ttk.Scale(
            controls_frame,
            from_=0.0,
            to=100.0,
            variable=self.dynamic_range_max,
            orient=tk.HORIZONTAL,
            length=300,
            command=lambda v: self.update_overlay()
        )
        dr_max_scale.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5)
        self.dr_max_label = ttk.Label(controls_frame, text="100.00")
        self.dr_max_label.grid(row=4, column=2, padx=5)
        self.dynamic_range_max.trace('w', lambda *args: self.dr_max_label.config(text=f"{self.dynamic_range_max.get():.1f}%"))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(
            buttons_frame,
            text="Save Overlay",
            command=self.save_overlay
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Reset",
            command=self.reset_parameters
        ).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(1, weight=1)
    
    def apply_dynamic_range(self, matrix):
        """Apply dynamic range to matrix (percentage-based clipping)."""
        dr_min = self.dynamic_range_min.get()
        dr_max = self.dynamic_range_max.get()
        
        # Calculate percentiles
        min_val = np.percentile(matrix, dr_min)
        max_val = np.percentile(matrix, dr_max)
        
        # Clip and normalize
        clipped = np.clip(matrix, min_val, max_val)
        if max_val > min_val:
            normalized = (clipped - min_val) / (max_val - min_val)
        else:
            normalized = np.zeros_like(clipped)
        
        return normalized * 255.0
    
    def update_overlay(self):
        """Update the overlay image based on current parameters."""
        # Get current matrix
        matrix = self.cumulative_matrix.copy()
        
        # Get min threshold to create mask
        min_thresh = self.min_threshold.get()
        max_thresh = self.max_threshold.get()
        
        # Create mask for values above min threshold
        mask = (matrix >= min_thresh).astype(np.uint8)
        
        # Apply min/max threshold to matrix
        matrix = np.clip(matrix, min_thresh, max_thresh)
        
        # Apply dynamic range
        matrix_normalized = self.apply_dynamic_range(matrix)
        matrix_u8 = matrix_normalized.astype(np.uint8)
        
        # Apply colormap
        colormap_dict = {
            "JET": cv2.COLORMAP_JET,
            "HOT": cv2.COLORMAP_HOT,
            "PLASMA": cv2.COLORMAP_PLASMA,
            "VIRIDIS": cv2.COLORMAP_VIRIDIS,
        }
        colormap = colormap_dict.get(config.COLORMAP.upper(), cv2.COLORMAP_JET)
        heatmap_bgr = cv2.applyColorMap(matrix_u8, colormap)
        
        # Create overlay
        base = self.representative_frame.copy()
        alpha_val = self.alpha.get()
        
        # Blend
        blended = cv2.addWeighted(base, 1.0 - alpha_val, heatmap_bgr, alpha_val, 0.0)
        
        # Apply mask: only show overlay where values >= min_threshold
        # Expand mask to 3 channels for color image
        mask_3d = mask[:, :, np.newaxis]
        
        # Where mask is 0 (below threshold), keep original image
        # Where mask is 1 (above threshold), use blended overlay
        overlay_bgr = base * (1 - mask_3d) + blended * mask_3d
        
        # Convert to RGB for display
        overlay_rgb = cv2.cvtColor(overlay_bgr, cv2.COLOR_BGR2RGB)
        
        # Resize for display if too large
        display_size = 800
        h, w = overlay_rgb.shape[:2]
        if w > display_size or h > display_size:
            scale = display_size / max(w, h)
            new_w, new_h = int(w * scale), int(h * scale)
            overlay_rgb = cv2.resize(overlay_rgb, (new_w, new_h))
        
        # Convert to PIL Image and display
        pil_image = Image.fromarray(overlay_rgb)
        photo = ImageTk.PhotoImage(image=pil_image)
        
        self.image_label.config(image=photo)
        self.image_label.image = photo  # Keep a reference
        
        self.current_overlay = overlay_bgr  # Store full resolution for saving (with mask applied)
    
    def save_overlay(self):
        """Save the current overlay to file."""
        folder_name = "2_insulators_4"
        output_folder = Path("results_for_users") / folder_name
        
        # Generate filename with parameters
        params = f"min{self.min_threshold.get():.1f}_max{self.max_threshold.get():.1f}_alpha{self.alpha.get():.2f}_dr{self.dynamic_range_min.get():.0f}-{self.dynamic_range_max.get():.0f}"
        output_file = output_folder / f"overlay_{params}.png"
        
        cv2.imwrite(str(output_file), self.current_overlay)
        print(f"Saved overlay to: {output_file}")
        
        # Show confirmation
        tkinter.messagebox.showinfo("Saved", f"Overlay saved to:\n{output_file}")
    
    def reset_parameters(self):
        """Reset all parameters to defaults."""
        self.min_threshold.set(0.0)
        self.max_threshold.set(float(self.cumulative_matrix.max()))
        self.alpha.set(0.55)
        self.dynamic_range_min.set(0.0)
        self.dynamic_range_max.set(100.0)
        self.update_overlay()


def main():
    """Main entry point for Process 2."""
    folder_name = "Prisma/615"
    folder_name = "Prisma/316"
    video_folder = Path("results_for_users") / folder_name
    
    matrix_file = video_folder / "cumulative_matrix.npy"
    frame_file = video_folder / "representative_frame.npy"
    
    if not matrix_file.exists():
        print(f"Error: Cumulative matrix not found: {matrix_file}")
        print("Please run Process 1 first to generate the cumulative matrix.")
        return
    
    if not frame_file.exists():
        print(f"Error: Representative frame not found: {frame_file}")
        print("Please run Process 1 first to generate the representative frame.")
        return
    
    # Create GUI
    root = tk.Tk()
    app = OverlayGUI(root, matrix_file, frame_file)
    root.mainloop()


if __name__ == "__main__":
    main()

