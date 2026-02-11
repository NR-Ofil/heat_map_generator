"""
Main GUI Application for Red-Spot Heatmap Processing.
Allows user to select a folder, process all videos, and view overlays interactively.
"""

import cv2
import numpy as np
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import config
from video_processor import (
    process_video,
    remove_persistent_pixels
)


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
        self.root.title("Red-Spot Heatmap Processor")
        self.root.geometry("600x500")
        
        self.selected_folder = None
        self.processed_videos = {}  # {video_name: {matrix_file, frame_file, output_folder}}
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create main GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Red-Spot Heatmap Processor", font=("Arial", 16, "bold"))
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
        
        # Process button
        self.process_button = ttk.Button(
            main_frame,
            text="Process All Videos",
            command=self.process_videos,
            state=tk.DISABLED
        )
        self.process_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Video list frame
        list_frame = ttk.LabelFrame(main_frame, text="Processed Videos", padding="10")
        list_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Listbox with scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.video_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10)
        self.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.video_listbox.yview)
        
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
        folder = filedialog.askdirectory(title="Select Folder with Videos")
        if folder:
            self.selected_folder = Path(folder)
            self.folder_label.config(text=str(self.selected_folder), foreground="black")
            self.process_button.config(state=tk.NORMAL)
            self.processed_videos = {}
            self.video_listbox.delete(0, tk.END)
            self.view_button.config(state=tk.DISABLED)
    
    def process_videos(self):
        """Process all videos in the selected folder."""
        if not self.selected_folder:
            messagebox.showerror("Error", "Please select a folder first.")
            return
        
        # Find all video files
        video_extensions = ['.mov', '.mp4', '.avi', '.mkv', '.webm']
        video_files = []
        for ext in video_extensions:
            video_files.extend(self.selected_folder.glob(f"*{ext}"))
            video_files.extend(self.selected_folder.glob(f"*{ext.upper()}"))
        
        if not video_files:
            messagebox.showwarning("No Videos", f"No video files found in {self.selected_folder}")
            return
        
        # Disable button and show progress
        self.process_button.config(state=tk.DISABLED)
        self.progress_label.config(text=f"Processing {len(video_files)} video(s)...")
        self.progress_bar.start()
        
        # Process in separate thread to keep GUI responsive
        thread = threading.Thread(target=self._process_videos_thread, args=(video_files,))
        thread.daemon = True
        thread.start()
    
    def _process_videos_thread(self, video_files):
        """Process videos in background thread."""
        try:
            for i, video_path in enumerate(video_files):
                try:
                    # Update progress
                    self.root.after(0, lambda v=video_path, n=i+1, total=len(video_files): 
                        self.progress_label.config(text=f"Processing {n}/{total}: {v.name}"))
                    
                    # Process video
                    acc, representative_frame, frames_processed, total_frames = process_video(str(video_path))
                    acc = remove_persistent_pixels(acc, frames_processed)
                    
                    # Save files
                    video_name = video_path.stem
                    matrix_file = self.selected_folder / f"{video_name}_matrix.npy"
                    frame_file = self.selected_folder / f"{video_name}_frame.npy"
                    
                    np.save(str(matrix_file), acc)
                    np.save(str(frame_file), representative_frame)
                    
                    # Store info
                    self.processed_videos[video_name] = {
                        'matrix_file': matrix_file,
                        'frame_file': frame_file,
                        'output_folder': self.selected_folder,
                        'video_path': video_path
                    }
                    
                    # Update listbox
                    self.root.after(0, lambda name=video_name: self.video_listbox.insert(tk.END, name))
                    
                except Exception as e:
                    print(f"Error processing {video_path}: {e}")
                    self.root.after(0, lambda v=video_path, err=str(e): 
                        messagebox.showerror("Processing Error", f"Error processing {v.name}:\n{err}"))
            
            # Done
            self.root.after(0, self._processing_complete)
            
        except Exception as e:
            self.root.after(0, lambda err=str(e): 
                messagebox.showerror("Error", f"Processing failed:\n{err}"))
            self.root.after(0, self._processing_complete)
    
    def _processing_complete(self):
        """Called when processing is complete."""
        self.progress_bar.stop()
        self.progress_label.config(text=f"Processing complete! {len(self.processed_videos)} video(s) processed.")
        self.process_button.config(state=tk.NORMAL)
        if self.processed_videos:
            self.view_button.config(state=tk.NORMAL)
    
    def view_overlay(self):
        """Open overlay GUI for selected video."""
        selection = self.video_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a video from the list.")
            return
        
        video_name = self.video_listbox.get(selection[0])
        if video_name not in self.processed_videos:
            messagebox.showerror("Error", f"Video {video_name} not found in processed videos.")
            return
        
        video_info = self.processed_videos[video_name]
        
        # Open overlay window
        overlay_window = tk.Toplevel(self.root)
        overlay_gui = OverlayGUI(
            overlay_window,
            video_info['matrix_file'],
            video_info['frame_file'],
            video_info['output_folder']
        )


def main():
    """Main entry point."""
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

