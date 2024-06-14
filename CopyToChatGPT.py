import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from ttkwidgets import CheckboxTreeview
import pyperclip
import json

def resource_path(relative_path):
    """Get absolute path to resource, works for development and for PyInstaller."""
    try:
        base_path = sys._MEIPASS  # PyInstaller creates a temp folder and stores path in _MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MultiFileCopierApp:
    CONFIG_FILE = "config.json"

    def __init__(self, root):
        """Initialize the MultiFileCopierApp with the given Tkinter root window."""
        self.root = root
        self.root.title("Copy to ChatGPT")

        # Set window icon
        icon_path = resource_path('robot_icon.png')
        self.root.iconphoto(False, tk.PhotoImage(file=icon_path))

        self.selected_folder = ""
        self.file_vars = {}

        # Load last directory
        self.load_config()

        # Frame for top buttons
        self.top_button_frame = tk.Frame(root)
        self.top_button_frame.pack(pady=10, padx=10, fill=tk.X)

        # Folder selection button
        self.folder_button = ttk.Button(self.top_button_frame, text="Select Folder", command=self.select_folder)
        self.folder_button.pack(side=tk.LEFT, padx=(0, 5))

        # Refresh files button
        self.refresh_button = ttk.Button(self.top_button_frame, text="Refresh Files", command=self.refresh_files)
        self.refresh_button.pack(side=tk.LEFT, padx=5)

        # Select all button
        self.select_all_button = ttk.Button(self.top_button_frame, text="Select All", command=self.select_all)
        self.select_all_button.pack(side=tk.LEFT, padx=5)

        # Deselect all button
        self.deselect_all_button = ttk.Button(self.top_button_frame, text="Deselect All", command=self.deselect_all)
        self.deselect_all_button.pack(side=tk.LEFT, padx=5)

        # File counter label
        self.file_counter_label = ttk.Label(self.top_button_frame, text="Selected Files: 0")
        self.file_counter_label.pack(side=tk.RIGHT, padx=5)

        # Frame for Treeview and scrollbar
        self.tree_frame = tk.Frame(root)
        self.tree_frame.pack(padx=10, fill=tk.BOTH, expand=True)

        # CheckboxTreeview widget
        self.tree = CheckboxTreeview(self.tree_frame)
        self.tree.heading('#0', text='Files and Folders', anchor='w')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for Treeview
        self.tree_scrollbar = tk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scrollbar.set)
        self.tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Frame for bottom buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=10, padx=10, fill=tk.X, side=tk.BOTTOM)

        # Copy selected files button
        self.copy_files_button = ttk.Button(self.button_frame, text="Copy Selected Files to Clipboard", command=self.copy_selected_files_to_clipboard)
        self.copy_files_button.pack(side=tk.LEFT, padx=(0, 5))

        # Copy folder structure button
        self.copy_structure_button = ttk.Button(self.button_frame, text="Copy Folder Structure to Clipboard", command=self.copy_folder_structure_to_clipboard)
        self.copy_structure_button.pack(side=tk.LEFT, padx=5)

        # Status bar
        self.status_bar = ttk.Label(root, text="Ready", relief=tk.SUNKEN, anchor='w')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10)

        # Bind tree events to update the file counter
        self.tree.bind('<<TreeviewSelect>>', self.update_file_counter)
        self.tree.bind('<<TreeviewItemCheck>>', self.update_file_counter)
        self.tree.bind('<<TreeviewItemUncheck>>', self.update_file_counter)

        # Load files if a directory was loaded
        if self.selected_folder:
            self.load_files()
            self.update_status_bar(f"Folder loaded: {self.selected_folder}")

    def save_config(self):
        """Save the current configuration to a JSON file."""
        config = {
            'last_directory': self.selected_folder
        }
        with open(self.CONFIG_FILE, 'w') as config_file:
            json.dump(config, config_file)

    def load_config(self):
        """Load the configuration from a JSON file."""
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, 'r') as config_file:
                config = json.load(config_file)
                self.selected_folder = config.get('last_directory', '')
        else:
            self.selected_folder = ''

    def select_folder(self):
        """Open a dialog to select a folder and load its files."""
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folder = folder
            self.save_config()
            try:
                self.load_files()
                self.update_status_bar(f"Folder loaded: {folder}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load folder: {e}")
                self.update_status_bar("Error loading folder")

    def refresh_files(self):
        """Refresh the list of files from the selected folder."""
        if self.selected_folder:
            try:
                self.load_files()
                self.update_status_bar(f"Files refreshed: {self.selected_folder}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to refresh files: {e}")
                self.update_status_bar("Error refreshing files")
        else:
            messagebox.showwarning("No folder selected", "Please select a folder first.")
            self.update_status_bar("No folder selected")

    def load_files(self):
        """Load files from the selected folder into the tree view."""
        self.tree.delete(*self.tree.get_children())
        self.file_vars.clear()
        self.add_files(self.selected_folder, "")
        self.apply_zebra_pattern()
        self.update_file_counter()

    def add_files(self, folder, parent_item):
        """Add files and folders to the tree view."""
        items = sorted(os.listdir(folder), key=lambda x: (not os.path.isdir(os.path.join(folder, x)), x.lower()))
        for item in items:
            item_path = os.path.join(folder, item)
            if os.path.isdir(item_path):
                item_id = self.tree.insert(parent_item, 'end', text=f"{item}/", open=False, tags=('unchecked',))
                self.add_files(item_path, item_id)
            else:
                item_id = self.tree.insert(parent_item, 'end', text=item, tags=('unchecked',))
                self.file_vars[item_path] = item_id

    def apply_zebra_pattern(self):
        """Apply a zebra pattern to the tree view."""
        for index, item in enumerate(self.tree.get_children()):
            if index % 2 == 0:
                self.tree.item(item, tags=('evenrow', 'unchecked'))
            else:
                self.tree.item(item, tags=('oddrow', 'unchecked'))
        self.tree.tag_configure('evenrow', background='#f9f9f9')
        self.tree.tag_configure('oddrow', background='#ffffff')

    def select_all(self):
        """Select all files and folders in the tree view."""
        self.change_state_all_items('checked')
        self.update_file_counter()

    def deselect_all(self):
        """Deselect all files and folders in the tree view."""
        self.change_state_all_items('unchecked')
        self.update_file_counter()

    def change_state_all_items(self, state):
        """Change the state of all items in the tree view."""
        for item in self.tree.get_children():
            self.change_state_recursive(item, state)

    def change_state_recursive(self, item, state):
        """Recursively change the state of items in the tree view."""
        self.tree.change_state(item, state)
        for child in self.tree.get_children(item):
            self.change_state_recursive(child, state)

    def update_file_counter(self, event=None):
        """Update the file counter label."""
        selected_count = sum(1 for path, item_id in self.file_vars.items() if 'checked' in self.tree.item(item_id, 'tags'))
        self.file_counter_label.config(text=f"Selected Files: {selected_count}")

    def update_status_bar(self, message):
        """Update the status bar with a message."""
        self.status_bar.config(text=message)

    def count_tokens(self, text):
        """Count the number of tokens in the text."""
        return len(text.split())

    def copy_selected_files_to_clipboard(self):
        """Copy the selected files to the clipboard."""
        included_files = [path for path, item_id in self.file_vars.items() if 'checked' in self.tree.item(item_id, 'tags')]
        if not included_files:
            messagebox.showwarning("No files selected", "Please select at least one file to copy.")
            self.update_status_bar("No files selected")
            return
        try:
            contents = ""
            for filepath in included_files:
                with open(filepath, 'r') as file:
                    contents += f"--- {os.path.relpath(filepath, self.selected_folder)} ---\n"
                    contents += file.read() + "\n\n"
            token_count = self.count_tokens(contents)
            pyperclip.copy(contents)
            self.update_status_bar(f"Files copied to clipboard. Approximate token count: {token_count}")
            messagebox.showinfo("Success", f"Files copied to clipboard. Approximate token count: {token_count}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy files to clipboard: {e}")
            self.update_status_bar("Error copying files")

    def generate_folder_structure(self, folder, indent=""):
        """Generate a string representing the folder structure."""
        folder_structure = ""
        items = sorted(os.listdir(folder), key=lambda x: (not os.path.isdir(os.path.join(folder, x)), x.lower()))
        for index, item in enumerate(items):
            item_path = os.path.join(folder, item)
            is_last = (index == len(items) - 1)
            if os.path.isdir(item_path):
                folder_structure += f"{indent}{'└── ' if is_last else '├── '}{item}/\n"
                folder_structure += self.generate_folder_structure(item_path, indent + ("    " if is_last else "│   "))
            else:
                folder_structure += f"{indent}{'└── ' if is_last else '├── '}{item}\n"
        return folder_structure

    def copy_folder_structure_to_clipboard(self):
        """Copy the folder structure to the clipboard."""
        if not self.selected_folder:
            messagebox.showwarning("No folder selected", "Please select a folder first.")
            self.update_status_bar("No folder selected")
            return
        try:
            folder_structure = self.generate_folder_structure(self.selected_folder)
            pyperclip.copy(folder_structure)
            self.update_status_bar("Folder structure copied to clipboard")
            messagebox.showinfo("Success", "Folder structure copied to clipboard.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy folder structure to clipboard: {e}")
            self.update_status_bar("Error copying folder structure")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = MultiFileCopierApp(root)
    root.mainloop()
