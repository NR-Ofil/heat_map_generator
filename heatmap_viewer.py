"""
Heatmap Viewer GUI Application.
Scans for existing matrix.npy and frame.npy files and allows viewing overlays.
"""

import cv2
import numpy as np
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import config


class OverlayGUI:
    """Interactive overlay GUI for a single video."""
    
    def __init__(self, root, matrix_file, frame_file, output_folder):
        self.root = root
        self.root.title("Red-Spot Heatmap Overlay - Interactive")
        self.output_folder = output_folder
        
        # Load data
        print(f"Loading cumulative matrix from: {matrix_file}")
        self.cumulative_matrix = np.load(str(matrix_file))
        print(f"Loading representative frame from: {frame_file}")
        self.representative_frame = np.load(str(frame_file))
        
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
        # Generate filename with parameters
        params = f"min{self.min_threshold.get():.1f}_max{self.max_threshold.get():.1f}_alpha{self.alpha.get():.2f}_dr{self.dynamic_range_min.get():.0f}-{self.dynamic_range_max.get():.0f}"
        output_file = self.output_folder / f"overlay_{params}.png"
        
        cv2.imwrite(str(output_file), self.current_overlay)
        print(f"Saved overlay to: {output_file}")
        
        # Show confirmation
        messagebox.showinfo("Saved", f"Overlay saved to:\n{output_file}")
    
    def reset_parameters(self):
        """Reset all parameters to defaults."""
        self.min_threshold.set(0.0)
        self.max_threshold.set(float(self.cumulative_matrix.max()))
        self.alpha.set(0.55)
        self.dynamic_range_min.set(0.0)
        self.dynamic_range_max.set(100.0)
        self.update_overlay()


class MainApp:
    """Main application GUI."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Heatmap Viewer")
        self.root.geometry("500x400")
        
        self.selected_folder = None
        self.available_files = {}  # {file_name: {matrix_file, frame_file, output_folder}}
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create main GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Heatmap Viewer", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Folder selection
        folder_frame = ttk.LabelFrame(main_frame, text="Folder Selection", padding="10")
        folder_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.folder_label = ttk.Label(folder_frame, text="No folder selected", foreground="gray")
        self.folder_label.grid(row=0, column=0, sticky=tk.W, padx=5)
        
        ttk.Button(
            folder_frame,
            text="Select Folder",
            command=self.select_folder
        ).grid(row=0, column=1, padx=5)
        
        # Scan button
        self.scan_button = ttk.Button(
            main_frame,
            text="Scan for .npy Files",
            command=self.scan_files,
            state=tk.DISABLED
        )
        self.scan_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="", foreground="blue")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=5)
        
        # File list frame
        list_frame = ttk.LabelFrame(main_frame, text="Available Files", padding="10")
        list_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Listbox with scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=8)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Double-click to open
        self.file_listbox.bind('<Double-Button-1>', lambda e: self.view_overlay())
        
        # View button
        self.view_button = ttk.Button(
            main_frame,
            text="View Overlay",
            command=self.view_overlay,
            state=tk.DISABLED
        )
        self.view_button.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
    
    def select_folder(self):
        """Open folder selection dialog."""
        folder = filedialog.askdirectory(title="Select Folder with .npy Files")
        if folder:
            self.selected_folder = Path(folder)
            self.folder_label.config(text=str(self.selected_folder), foreground="black")
            self.scan_button.config(state=tk.NORMAL)
            self.available_files = {}
            self.file_listbox.delete(0, tk.END)
            self.view_button.config(state=tk.DISABLED)
            self.status_label.config(text="")
    
    def scan_files(self):
        """Scan folder for matrix.npy and frame.npy files."""
        if not self.selected_folder:
            messagebox.showerror("Error", "Please select a folder first.")
            return
        
        # Find all matrix and frame files
        matrix_files = list(self.selected_folder.glob("*_matrix.npy"))
        frame_files = list(self.selected_folder.glob("*_frame.npy"))
        
        # Also check for files named just "matrix.npy" and "frame.npy" or "cumulative_matrix.npy" and "representative_frame.npy"
        matrix_files.extend(self.selected_folder.glob("matrix.npy"))
        matrix_files.extend(self.selected_folder.glob("cumulative_matrix.npy"))
        frame_files.extend(self.selected_folder.glob("frame.npy"))
        frame_files.extend(self.selected_folder.glob("representative_frame.npy"))
        
        # Match pairs
        self.available_files = {}
        
        # Match files with pattern: name_matrix.npy and name_frame.npy
        matrix_dict = {}
        for mf in matrix_files:
            if mf.name == "matrix.npy" or mf.name == "cumulative_matrix.npy":
                # Special case: look for matching frame file
                if mf.name == "matrix.npy":
                    frame_file = self.selected_folder / "frame.npy"
                else:  # cumulative_matrix.npy
                    frame_file = self.selected_folder / "representative_frame.npy"
                
                if frame_file.exists():
                    name = mf.stem.replace("_matrix", "").replace("cumulative_", "")
                    self.available_files[name] = {
                        'matrix_file': mf,
                        'frame_file': frame_file,
                        'output_folder': self.selected_folder
                    }
            else:
                # Extract base name (remove _matrix suffix)
                base_name = mf.stem.replace("_matrix", "")
                matrix_dict[base_name] = mf
        
        # Match with frame files
        for ff in frame_files:
            if ff.name == "frame.npy" or ff.name == "representative_frame.npy":
                continue  # Already handled above
            
            # Extract base name (remove _frame suffix)
            base_name = ff.stem.replace("_frame", "").replace("representative_", "")
            
            if base_name in matrix_dict:
                self.available_files[base_name] = {
                    'matrix_file': matrix_dict[base_name],
                    'frame_file': ff,
                    'output_folder': self.selected_folder
                }
        
        # Update UI
        self.file_listbox.delete(0, tk.END)
        if self.available_files:
            for file_name in sorted(self.available_files.keys()):
                self.file_listbox.insert(tk.END, file_name)
            self.status_label.config(
                text=f"Found {len(self.available_files)} file pair(s)",
                foreground="green"
            )
            self.view_button.config(state=tk.NORMAL)
        else:
            self.status_label.config(
                text="No matching matrix.npy and frame.npy files found",
                foreground="red"
            )
            self.view_button.config(state=tk.DISABLED)
    
    def view_overlay(self):
        """Open overlay GUI for selected file."""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file from the list.")
            return
        
        file_name = self.file_listbox.get(selection[0])
        if file_name not in self.available_files:
            messagebox.showerror("Error", f"File {file_name} not found in available files.")
            return
        
        file_info = self.available_files[file_name]
        
        # Verify files exist
        if not file_info['matrix_file'].exists():
            messagebox.showerror("Error", f"Matrix file not found: {file_info['matrix_file']}")
            return
        
        if not file_info['frame_file'].exists():
            messagebox.showerror("Error", f"Frame file not found: {file_info['frame_file']}")
            return
        
        # Open overlay window
        overlay_window = tk.Toplevel(self.root)
        overlay_gui = OverlayGUI(
            overlay_window,
            file_info['matrix_file'],
            file_info['frame_file'],
            file_info['output_folder']
        )


def main():
    """Main entry point."""
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

