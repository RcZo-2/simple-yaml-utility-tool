import tkinter as tk
from tkinter import filedialog, messagebox
import yaml
import os
import json
import re
import shutil

# Global variables
yaml_file_path = None


def load_yaml(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load YAML: {str(e)}")
        return None


def save_yaml(original_path, data):
    base_dir = os.path.dirname(original_path)
    output_dir = os.path.join(base_dir, "result")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, os.path.basename(original_path))

    try:
        with open(f"{output_path}.tmp", 'w') as tmp_file:
            yaml.dump(data, tmp_file, default_flow_style=False)
        shutil.move(f"{output_path}.tmp", output_path)
        messagebox.showinfo("Success", f"File saved to {output_path}")
    except Exception as e:
        if os.path.exists(f"{output_path}.tmp"):
            os.remove(f"{output_path}.tmp")
        messagebox.showerror("Error", f"Failed to save: {str(e)}")


def replace_value_at_location(data, location, new_value):
    keys = re.findall(r'\w+|\[\d+\]', location)
    current = data
    for i, key in enumerate(keys[:-1]):
        if key.startswith('[') and key.endswith(']'):
            try:
                idx = int(key[1:-1])
                if not isinstance(current, list) or idx >= len(current):
                    raise ValueError(f"Invalid index {key} at path segment {i + 1}")
                current = current[idx]
            except Exception as e:
                raise ValueError(f"Error parsing index {key}: {str(e)}")
        else:
            if not isinstance(current, dict) or key not in current:
                raise KeyError(f"Key '{key}' not found at segment {i + 1}")
            current = current[key]

    last_key = keys[-1]
    if last_key.startswith('[') and last_key.endswith(']'):
        try:
            idx = int(last_key[1:-1])
            if not isinstance(current, list) or idx >= len(current):
                raise ValueError(f"Invalid index {last_key}")
            current[idx] = new_value
        except Exception as e:
            raise ValueError(f"Error parsing index {last_key}: {str(e)}")
    else:
        if not isinstance(current, dict):
            raise TypeError(f"Expected dict at final segment, got {type(current).__name__}")
        current[last_key] = new_value


def browse_file():
    global yaml_file_path
    path = filedialog.askopenfilename(filetypes=[("YAML Files", "*.yaml *.yml")])
    if path:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, path)
        yaml_file_path = path


def search_value():
    path = file_entry.get()
    value = value_entry.get()
    if not path or not value:
        messagebox.showwarning("Error", "Provide both file and search value")
        return

    data = load_yaml(path)
    if not data:
        return

    found = []

    def _search(d, current_path):
        if isinstance(d, dict):
            for k, v in d.items():
                new_path = f"{current_path}.{k}" if current_path else k
                if v == value:
                    found.append(new_path)
                _search(v, new_path)
        elif isinstance(d, list):
            for idx, item in enumerate(d):
                new_path = f"{current_path}[{idx}]" if current_path else f"[{idx}]"
                if item == value:
                    found.append(new_path)
                _search(item, new_path)

    _search(data, "")

    if found:
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"Found at:\n" + "\n".join(found))
        result_text.config(state=tk.DISABLED)
    else:
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Not found")
        result_text.config(state=tk.DISABLED)


def select_json():
    global batch_json_path
    path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if path:
        batch_json_path = path
        json_entry.delete(0, tk.END)
        json_entry.insert(0, path)


def perform_replace():
    global yaml_file_path
    if not yaml_file_path:
        messagebox.showerror("Error", "Please select a YAML file first")
        return

    try:
        data = load_yaml(yaml_file_path)
        if not data:
            return

        if mode_var.get() == "single":
            loc = location_entry.get().strip()
            new_val = new_value_entry.get().strip()
            if not loc or not new_val:
                messagebox.showwarning("Error", "Provide location and new value")
                return

            replace_value_at_location(data, loc, new_val)

        elif mode_var.get() == "batch":
            if not batch_json_path:
                messagebox.showwarning("Error", "Select a batch JSON file")
                return

            with open(batch_json_path, 'r') as f:
                batch_ops = json.load(f)

            errors = []
            for op in batch_ops:
                loc = op.get("location")
                new_val = op.get("new_value")
                if not loc or not new_val:
                    errors.append(f"Invalid entry: missing 'location' or 'new_value'")
                    continue

                try:
                    replace_value_at_location(data, loc, new_val)
                except Exception as e:
                    errors.append(f"Failed {loc}: {str(e)}")

            if errors:
                messagebox.showerror("Batch Errors", "\n".join(errors))

        save_yaml(yaml_file_path, data)

    except Exception as e:
        messagebox.showerror("Error", f"Replacement failed: {str(e)}")


# GUI setup
root = tk.Tk()
root.title("YAML Search & Replace Tool")
root.geometry("900x600")

# File Selection
tk.Label(root, text="YAML File:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
file_entry = tk.Entry(root, width=60)
file_entry.grid(row=0, column=1, padx=10, pady=10)
browse_button = tk.Button(root, text="Browse", command=browse_file)
browse_button.grid(row=0, column=2, padx=10, pady=10)

# Search Section
tk.Label(root, text="Search Value:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
value_entry = tk.Entry(root, width=60)
value_entry.grid(row=1, column=1, padx=10, pady=10)
search_button = tk.Button(root, text="Search", command=search_value)
search_button.grid(row=1, column=2, padx=10, pady=10)

# Result Display
result_text = tk.Text(root, height=6, width=70, state=tk.DISABLED)
result_text.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="we")

# Mode Selection
mode_var = tk.StringVar(value="single")
tk.Radiobutton(root, text="Single Replacement", variable=mode_var, value="single").grid(row=3, column=0, padx=10,
                                                                                        pady=10, sticky="w")
tk.Radiobutton(root, text="Batch Replacement", variable=mode_var, value="batch").grid(row=3, column=1, padx=10, pady=10,
                                                                                      sticky="w")

# Single Replacement Inputs
location_frame = tk.Frame(root)
location_label = tk.Label(location_frame, text="Location:")
location_entry = tk.Entry(location_frame, width=50)
location_label.pack(side=tk.LEFT)
location_entry.pack(side=tk.LEFT, padx=5)
new_value_label = tk.Label(location_frame, text="New Value:")
new_value_entry = tk.Entry(location_frame, width=50)
new_value_label.pack(side=tk.LEFT)
new_value_entry.pack(side=tk.LEFT, padx=5)
location_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="w")

# Batch Replacement Inputs
batch_frame = tk.Frame(root)
batch_label = tk.Label(batch_frame, text="Batch JSON:")
json_entry = tk.Entry(batch_frame, width=50, state=tk.DISABLED)
json_btn = tk.Button(batch_frame, text="Select JSON", command=select_json, state=tk.DISABLED)
batch_label.pack(side=tk.LEFT)
json_entry.pack(side=tk.LEFT, padx=5)
json_btn.pack(side=tk.LEFT, padx=5)
batch_frame.grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky="w")


# Mode Toggle
def toggle_mode(*args):
    if mode_var.get() == "batch":
        location_frame.grid_remove()
        batch_frame.grid()
        json_entry.config(state=tk.NORMAL)
        json_btn.config(state=tk.NORMAL)
    else:
        batch_frame.grid_remove()
        location_frame.grid()
        json_entry.config(state=tk.DISABLED)
        json_btn.config(state=tk.DISABLED)


mode_var.trace("w", toggle_mode)

# Replace Button
replace_button = tk.Button(root, text="Replace", command=perform_replace)
replace_button.grid(row=6, column=1, padx=10, pady=20)

root.mainloop()