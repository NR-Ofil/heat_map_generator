"""
Video Processor GUI Application.
Processes .mov files: allows frame selection and creates matrix.npy files.
"""

import cv2
import numpy as np
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import subprocess
import sys
import config
from video_processor import (
    process_video,
    remove_persistent_pixels
)


class FrameViewer:
    """Frame-by-frame viewer for selecting representative frame."""
    
    def __init__(self, root, video_path, output_folder):
        self.root = root
        self.root.title(f"Frame Viewer - {Path(video_path).name}")
        self.video_path = video_path
        self.output_folder = output_folder
        self.video_name = Path(video_path).stem
        
        # Open video
        self.cap = cv2.VideoCapture(str(video_path))
        if not self.cap.isOpened():
            messagebox.showerror("Error", f"Unable to open video: {video_path}")
            self.root.destroy()
            return
        
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame_idx = 0
        self.selected_frame_idx = None
        self.selected_frame = None
        
        # Create GUI first (needed for load_frame)
        self.create_widgets()
        
        # Load first frame after GUI is created
        self.load_frame(0)
    
    def create_widgets(self):
        """Create GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Image display
        image_frame = ttk.Frame(main_frame)
        image_frame.grid(row=0, column=0, columnspan=3, pady=10)
        
        self.image_label = ttk.Label(image_frame)
        self.image_label.pack()
        
        # Frame info
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=1, column=0, columnspan=3, pady=5)
        
        self.frame_info_label = ttk.Label(info_frame, text="", font=("Arial", 10))
        self.frame_info_label.pack()
        
        # Navigation controls
        nav_frame = ttk.Frame(main_frame)
        nav_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(nav_frame, text="⏮ First", command=lambda: self.load_frame(0)).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="⏪ Prev", command=self.prev_frame).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="⏩ Next", command=self.next_frame).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="⏭ Last", command=lambda: self.load_frame(self.total_frames - 1)).pack(side=tk.LEFT, padx=5)
        
        # Frame slider
        slider_frame = ttk.Frame(main_frame)
        slider_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10, padx=20)
        
        ttk.Label(slider_frame, text="Frame:").pack(side=tk.LEFT, padx=5)
        self.frame_slider = ttk.Scale(
            slider_frame,
            from_=0,
            to=max(0, self.total_frames - 1),
            orient=tk.HORIZONTAL,
            length=400,
            command=self.on_slider_change
        )
        self.frame_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.frame_number_label = ttk.Label(slider_frame, text="0")
        self.frame_number_label.pack(side=tk.LEFT, padx=5)
        
        # Selection controls
        select_frame = ttk.LabelFrame(main_frame, text="Frame Selection", padding="10")
        select_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        self.select_label = ttk.Label(select_frame, text="No frame selected", foreground="gray")
        self.select_label.pack(pady=5)
        
        ttk.Button(
            select_frame,
            text="Select This Frame",
            command=self.select_current_frame
        ).pack(pady=5)
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        self.process_button = ttk.Button(
            action_frame,
            text="Process Video & Create Matrix",
            command=self.process_video,
            state=tk.DISABLED
        )
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="Cancel",
            command=self.root.destroy
        ).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        slider_frame.columnconfigure(1, weight=1)
    
    def load_frame(self, frame_idx):
        """Load and display a specific frame."""
        if frame_idx < 0 or frame_idx >= self.total_frames:
            return
        
        self.current_frame_idx = frame_idx
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.cap.read()
        
        if not ret:
            return
        
        # Update display
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize for display if too large
        display_size = 800
        h, w = frame_rgb.shape[:2]
        if w > display_size or h > display_size:
            scale = display_size / max(w, h)
            new_w, new_h = int(w * scale), int(h * scale)
            frame_rgb = cv2.resize(frame_rgb, (new_w, new_h))
        
        pil_image = Image.fromarray(frame_rgb)
        photo = ImageTk.PhotoImage(image=pil_image)
        
        self.image_label.config(image=photo)
        self.image_label.image = photo
        
        # Update info
        self.frame_info_label.config(
            text=f"Frame {frame_idx + 1} / {self.total_frames}"
        )
        self.frame_number_label.config(text=str(frame_idx))
        self.frame_slider.set(frame_idx)
    
    def on_slider_change(self, value):
        """Handle slider change."""
        frame_idx = int(float(value))
        if frame_idx != self.current_frame_idx:
            self.load_frame(frame_idx)
    
    def prev_frame(self):
        """Load previous frame."""
        if self.current_frame_idx > 0:
            self.load_frame(self.current_frame_idx - 1)
    
    def next_frame(self):
        """Load next frame."""
        if self.current_frame_idx < self.total_frames - 1:
            self.load_frame(self.current_frame_idx + 1)
    
    def select_current_frame(self):
        """Select current frame as representative frame."""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_idx)
        ret, frame = self.cap.read()
        
        if ret:
            self.selected_frame_idx = self.current_frame_idx
            self.selected_frame = frame.copy()
            self.select_label.config(
                text=f"Frame {self.current_frame_idx + 1} selected",
                foreground="green"
            )
            self.process_button.config(state=tk.NORMAL)
    
    def process_video(self):
        """Process video and create matrix.npy file."""
        if self.selected_frame is None:
            messagebox.showwarning("No Frame Selected", "Please select a representative frame first.")
            return
        
        # Disable button
        self.process_button.config(state=tk.DISABLED, text="Processing...")
        self.root.update()
        
        # Process in separate thread
        thread = threading.Thread(target=self._process_video_thread)
        thread.daemon = True
        thread.start()
    
    def _process_video_thread(self):
        """Process video in background thread."""
        try:
            # Process video
            self.root.after(0, lambda: self.process_button.config(text="Processing video..."))
            acc, _, frames_processed, total_frames = process_video(str(self.video_path))
            
            # Remove persistent pixels
            self.root.after(0, lambda: self.process_button.config(text="Removing persistent pixels..."))
            acc = remove_persistent_pixels(acc, frames_processed)
            
            # Save files
            matrix_file = self.output_folder / f"{self.video_name}_matrix.npy"
            frame_file = self.output_folder / f"{self.video_name}_frame.npy"
            
            self.root.after(0, lambda: self.process_button.config(text="Saving files..."))
            np.save(str(matrix_file), acc)
            np.save(str(frame_file), self.selected_frame)
            
            # Success
            self.root.after(0, lambda: self._processing_complete(matrix_file, frame_file))
            
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror("Error", f"Processing failed:\n{err}"))
            self.root.after(0, lambda: self.process_button.config(state=tk.NORMAL, text="Process Video & Create Matrix"))
    
    def _processing_complete(self, matrix_file, frame_file):
        """Called when processing is complete."""
        self.process_button.config(state=tk.NORMAL, text="Process Video & Create Matrix")
        messagebox.showinfo(
            "Processing Complete",
            f"Files created:\n{matrix_file.name}\n{frame_file.name}\n\nYou can now view the overlay."
        )
        self.root.destroy()
    
    def __del__(self):
        """Cleanup: release video capture."""
        if hasattr(self, 'cap'):
            self.cap.release()


class MainApp:
    """Main application GUI."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Video Processor")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)
        
        self.selected_folder = None
        self.unprocessed_videos = []
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create main GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Video Processor", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Step 1: Folder selection
        folder_frame = ttk.LabelFrame(main_frame, text="Step 1: Choose Folder", padding="10")
        folder_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.folder_label = ttk.Label(folder_frame, text="No folder selected", foreground="gray")
        self.folder_label.grid(row=0, column=0, sticky=tk.W, padx=5)
        
        ttk.Button(
            folder_frame,
            text="Select Folder",
            command=self.select_folder
        ).grid(row=0, column=1, padx=5)
        
        # Step 2: Scan for unprocessed videos
        scan_frame = ttk.LabelFrame(main_frame, text="Step 2: Find Unprocessed Videos", padding="10")
        scan_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.scan_button = ttk.Button(
            scan_frame,
            text="Scan for .mov Files",
            command=self.scan_videos,
            state=tk.DISABLED
        )
        self.scan_button.pack()
        
        self.status_label = ttk.Label(scan_frame, text="", foreground="blue")
        self.status_label.pack(pady=5)
        
        # Video list
        list_frame = ttk.LabelFrame(main_frame, text="Unprocessed Videos", padding="10")
        list_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Create a frame for listbox and scrollbar
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.video_listbox = tk.Listbox(
            list_container, 
            yscrollcommand=scrollbar.set, 
            height=15, 
            width=70,
            selectmode=tk.SINGLE,
            font=("Arial", 10)
        )
        self.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.video_listbox.yview)
        
        # Add placeholder text
        self.video_listbox.insert(0, "Select folder and scan for videos...")
        self.video_listbox.config(state=tk.DISABLED)
        
        # Double-click to process
        self.video_listbox.bind('<Double-Button-1>', lambda e: self.process_selected_video())
        
        # Process button
        self.process_button = ttk.Button(
            main_frame,
            text="Process Selected Video",
            command=self.process_selected_video,
            state=tk.DISABLED
        )
        self.process_button.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Open viewer button
        self.viewer_button = ttk.Button(
            main_frame,
            text="Open Heatmap Viewer",
            command=self.open_viewer
        )
        self.viewer_button.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
    
    def select_folder(self):
        """Open folder selection dialog."""
        folder = filedialog.askdirectory(title="Select Folder with Videos")
        if folder:
            self.selected_folder = Path(folder)
            self.folder_label.config(text=str(self.selected_folder), foreground="black")
            self.scan_button.config(state=tk.NORMAL)
            self.unprocessed_videos = []
            self.video_listbox.config(state=tk.NORMAL)
            self.video_listbox.delete(0, tk.END)
            self.video_listbox.insert(0, "Click 'Scan for .mov Files' to find videos...")
            self.video_listbox.config(state=tk.DISABLED)
            self.process_button.config(state=tk.DISABLED)
            self.status_label.config(text="")
    
    def scan_videos(self):
        """Scan for .mov files without associated _matrix.npy files."""
        if not self.selected_folder:
            messagebox.showerror("Error", "Please select a folder first.")
            return
        
        # Find all video files (use set to avoid duplicates on case-insensitive filesystems)
        video_files = set()
        video_files.update(self.selected_folder.glob("*.mov"))
        video_files.update(self.selected_folder.glob("*.MOV"))
        video_files.update(self.selected_folder.glob("*.mp4"))
        video_files.update(self.selected_folder.glob("*.MP4"))
        
        # Convert to list and sort
        video_files = sorted(list(video_files))
        
        # Filter: only videos without _matrix.npy files
        self.unprocessed_videos = []
        for video_path in video_files:
            video_name = video_path.stem
            matrix_file = self.selected_folder / f"{video_name}_matrix.npy"
            if not matrix_file.exists():
                self.unprocessed_videos.append(video_path)
        
        # Update UI
        self.video_listbox.config(state=tk.NORMAL)
        self.video_listbox.delete(0, tk.END)
        if self.unprocessed_videos:
            # Sort by name for consistent display
            sorted_videos = sorted(self.unprocessed_videos, key=lambda p: p.name)
            for video_path in sorted_videos:
                self.video_listbox.insert(tk.END, video_path.name)
            self.status_label.config(
                text=f"Found {len(self.unprocessed_videos)} unprocessed video(s)",
                foreground="green"
            )
            self.process_button.config(state=tk.NORMAL)
            # Ensure listbox is visible
            self.video_listbox.see(0)
        else:
            self.video_listbox.insert(tk.END, "(No unprocessed videos found)")
            self.video_listbox.config(state=tk.DISABLED)
            self.status_label.config(
                text="All videos are processed or no videos found",
                foreground="blue"
            )
            self.process_button.config(state=tk.DISABLED)
    
    def process_selected_video(self):
        """Open frame viewer for selected video."""
        selection = self.video_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a video from the list.")
            return
        
        # Get the selected video name and find the corresponding path
        selected_name = self.video_listbox.get(selection[0])
        video_path = None
        for vp in self.unprocessed_videos:
            if vp.name == selected_name:
                video_path = vp
                break
        
        if video_path is None:
            messagebox.showerror("Error", f"Could not find video: {selected_name}")
            return
        
        # Open frame viewer window
        viewer_window = tk.Toplevel(self.root)
        frame_viewer = FrameViewer(viewer_window, video_path, self.selected_folder)
        
        # After viewer closes, refresh the list
        viewer_window.protocol("WM_DELETE_WINDOW", lambda: self._on_viewer_close(selection[0], viewer_window))
    
    def _on_viewer_close(self, selection_idx, window):
        """Handle viewer window close."""
        window.destroy()
        # Refresh the list after a short delay to allow file system to update
        self.root.after(500, self.scan_videos)
    
    def open_viewer(self):
        """Open the heatmap viewer app."""
        if getattr(sys, 'frozen', False):
            # Running as a bundled exe — launch the companion HeatmapViewer.exe
            viewer_exe = Path(sys.executable).parent / "HeatmapViewer.exe"
            if viewer_exe.exists():
                subprocess.Popen([str(viewer_exe)])
            else:
                messagebox.showerror(
                    "Error",
                    f"HeatmapViewer.exe not found next to this application.\n"
                    f"Expected: {viewer_exe}"
                )
        else:
            # Running as a script — open viewer inline as a child window
            from heatmap_viewer import MainApp as HeatmapViewerApp
            viewer_window = tk.Toplevel(self.root)
            HeatmapViewerApp(viewer_window)


def main():
    """Main entry point."""
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

