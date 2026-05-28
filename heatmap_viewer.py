"""
Heatmap Viewer GUI Application.
Scans for existing _matrix.npy and _frame.npy file pairs and allows viewing overlays.
"""

from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from overlay_gui import OverlayGUI


class MainApp:
    """Main application GUI."""

    def __init__(self, root):
        self.root = root
        self.root.title("Heatmap Viewer")
        self.root.geometry("500x400")

        self.selected_folder = None
        self.available_files = {}  # {name: {matrix_file, frame_file, output_folder}}

        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text="Heatmap Viewer", font=("Arial", 16, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 20)
        )

        folder_frame = ttk.LabelFrame(main_frame, text="Folder Selection", padding="10")
        folder_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        self.folder_label = ttk.Label(folder_frame, text="No folder selected", foreground="gray")
        self.folder_label.grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Button(folder_frame, text="Select Folder", command=self.select_folder).grid(row=0, column=1, padx=5)

        self.scan_button = ttk.Button(
            main_frame, text="Scan for .npy Files", command=self.scan_files, state=tk.DISABLED
        )
        self.scan_button.grid(row=2, column=0, columnspan=2, pady=10)

        self.status_label = ttk.Label(main_frame, text="", foreground="blue")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=5)

        list_frame = ttk.LabelFrame(main_frame, text="Available Files", padding="10")
        list_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=8)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        self.file_listbox.bind('<Double-Button-1>', lambda e: self.view_overlay())

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
        if not self.selected_folder:
            messagebox.showerror("Error", "Please select a folder first.")
            return

        matrix_files = list(self.selected_folder.glob("*_matrix.npy"))
        frame_files = list(self.selected_folder.glob("*_frame.npy"))

        # Also accept legacy naming (cumulative_matrix.npy / representative_frame.npy)
        matrix_files += list(self.selected_folder.glob("cumulative_matrix.npy"))
        frame_files  += list(self.selected_folder.glob("representative_frame.npy"))

        self.available_files = {}

        # Match legacy pair
        for mf in matrix_files:
            if mf.name == "cumulative_matrix.npy":
                ff = self.selected_folder / "representative_frame.npy"
                if ff.exists():
                    self.available_files["matrix"] = {
                        'matrix_file': mf, 'frame_file': ff,
                        'output_folder': self.selected_folder
                    }

        # Match {name}_matrix.npy + {name}_frame.npy pairs
        matrix_dict = {mf.stem.replace("_matrix", ""): mf for mf in matrix_files if "_matrix" in mf.name}
        for ff in frame_files:
            if "_frame" not in ff.name:
                continue
            base = ff.stem.replace("_frame", "")
            if base in matrix_dict:
                self.available_files[base] = {
                    'matrix_file': matrix_dict[base],
                    'frame_file': ff,
                    'output_folder': self.selected_folder,
                }

        self.file_listbox.delete(0, tk.END)
        if self.available_files:
            for name in sorted(self.available_files):
                self.file_listbox.insert(tk.END, name)
            self.status_label.config(text=f"Found {len(self.available_files)} file pair(s)", foreground="green")
            self.view_button.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="No matching matrix/frame .npy pairs found", foreground="red")
            self.view_button.config(state=tk.DISABLED)

    def view_overlay(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file from the list.")
            return

        name = self.file_listbox.get(selection[0])
        info = self.available_files.get(name)
        if not info:
            messagebox.showerror("Error", f"Entry '{name}' not found.")
            return

        if not info['matrix_file'].exists():
            messagebox.showerror("Error", f"Matrix file not found:\n{info['matrix_file']}")
            return
        if not info['frame_file'].exists():
            messagebox.showerror("Error", f"Frame file not found:\n{info['frame_file']}")
            return

        overlay_window = tk.Toplevel(self.root)
        OverlayGUI(overlay_window, info['matrix_file'], info['frame_file'], info['output_folder'])


def main():
    root = tk.Tk()
    MainApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
