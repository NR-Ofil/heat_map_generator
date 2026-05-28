"""
Main GUI Application for Red-Spot Heatmap Processing.
Allows user to select a folder, process all videos, and view overlays interactively.
"""

import numpy as np
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from video_processor import process_video, remove_persistent_pixels
from overlay_gui import OverlayGUI


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
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text="Red-Spot Heatmap Processor", font=("Arial", 16, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 20)
        )

        folder_frame = ttk.LabelFrame(main_frame, text="Folder Selection", padding="10")
        folder_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.folder_label = ttk.Label(folder_frame, text="No folder selected", foreground="gray")
        self.folder_label.grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Button(folder_frame, text="Select Folder", command=self.select_folder).grid(row=0, column=1, padx=5)

        self.process_button = ttk.Button(
            main_frame, text="Process All Videos", command=self.process_videos, state=tk.DISABLED
        )
        self.process_button.grid(row=2, column=0, columnspan=2, pady=10)

        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack()
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)

        list_frame = ttk.LabelFrame(main_frame, text="Processed Videos", padding="10")
        list_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.video_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10)
        self.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.video_listbox.yview)

        self.view_button = ttk.Button(
            main_frame, text="View Overlay", command=self.view_overlay, state=tk.DISABLED
        )
        self.view_button.grid(row=5, column=0, columnspan=2, pady=10)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Videos")
        if folder:
            self.selected_folder = Path(folder)
            self.folder_label.config(text=str(self.selected_folder), foreground="black")
            self.process_button.config(state=tk.NORMAL)
            self.processed_videos = {}
            self.video_listbox.delete(0, tk.END)
            self.view_button.config(state=tk.DISABLED)

    def process_videos(self):
        if not self.selected_folder:
            messagebox.showerror("Error", "Please select a folder first.")
            return

        video_extensions = ['.mov', '.mp4', '.avi', '.mkv', '.webm']
        video_files = []
        for ext in video_extensions:
            video_files.extend(self.selected_folder.glob(f"*{ext}"))
            video_files.extend(self.selected_folder.glob(f"*{ext.upper()}"))

        if not video_files:
            messagebox.showwarning("No Videos", f"No video files found in {self.selected_folder}")
            return

        self.process_button.config(state=tk.DISABLED)
        self.progress_label.config(text=f"Processing {len(video_files)} video(s)...")
        self.progress_bar.start()

        thread = threading.Thread(target=self._process_videos_thread, args=(video_files,))
        thread.daemon = True
        thread.start()

    def _process_videos_thread(self, video_files):
        try:
            for i, video_path in enumerate(video_files):
                try:
                    self.root.after(0, lambda v=video_path, n=i + 1, total=len(video_files):
                        self.progress_label.config(text=f"Processing {n}/{total}: {v.name}"))

                    acc, representative_frame, frames_processed, _ = process_video(str(video_path))
                    acc = remove_persistent_pixels(acc, frames_processed)

                    video_name = video_path.stem
                    matrix_file = self.selected_folder / f"{video_name}_matrix.npy"
                    frame_file = self.selected_folder / f"{video_name}_frame.npy"
                    np.save(str(matrix_file), acc)
                    np.save(str(frame_file), representative_frame)

                    self.processed_videos[video_name] = {
                        'matrix_file': matrix_file,
                        'frame_file': frame_file,
                        'output_folder': self.selected_folder,
                    }
                    self.root.after(0, lambda name=video_name: self.video_listbox.insert(tk.END, name))

                except Exception as e:
                    self.root.after(0, lambda v=video_path, err=str(e):
                        messagebox.showerror("Processing Error", f"Error processing {v.name}:\n{err}"))

            self.root.after(0, self._processing_complete)

        except Exception as e:
            self.root.after(0, lambda err=str(e):
                messagebox.showerror("Error", f"Processing failed:\n{err}"))
            self.root.after(0, self._processing_complete)

    def _processing_complete(self):
        self.progress_bar.stop()
        self.progress_label.config(text=f"Processing complete! {len(self.processed_videos)} video(s) processed.")
        self.process_button.config(state=tk.NORMAL)
        if self.processed_videos:
            self.view_button.config(state=tk.NORMAL)

    def view_overlay(self):
        selection = self.video_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a video from the list.")
            return

        video_name = self.video_listbox.get(selection[0])
        if video_name not in self.processed_videos:
            messagebox.showerror("Error", f"Video {video_name} not found in processed videos.")
            return

        video_info = self.processed_videos[video_name]
        overlay_window = tk.Toplevel(self.root)
        OverlayGUI(
            overlay_window,
            video_info['matrix_file'],
            video_info['frame_file'],
            video_info['output_folder'],
        )


def main():
    root = tk.Tk()
    MainApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
