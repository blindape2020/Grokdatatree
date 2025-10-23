import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, filedialog
import base64
from io import BytesIO
try:
    from PIL import Image, ImageTk
except ImportError:
    pass  # User needs to install Pillow

class DataTreeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DataTree")
        self.data_file = 'datatree.json'
        self.tree_data = self.load_tree(self.data_file)
        
        # Maximize window
        self.root.state('zoomed')
        
        # GUI Layout
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure root to expand main_frame
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Tree Display
        self.treeview = ttk.Treeview(self.main_frame, columns=("Content",), show="tree")
        self.treeview.column("Content", width=200, stretch=True)
        self.treeview.heading("Content", text="Content")
        self.treeview.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.treeview.yview)
        self.treeview.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=3, sticky=(tk.N, tk.S))
        
        # Bindings
        self.treeview.bind("<Double-Button-1>", self.view_entry)
        self.treeview.bind("<Button-3>", self.on_right_click)
        self.treeview.bind("<space>", self.toggle_tree)
        
        # Buttons
        ttk.Button(self.main_frame, text="New Folder", command=self.add_folder).grid(row=1, column=0, pady=5, sticky=tk.W)
        ttk.Button(self.main_frame, text="New Entry", command=self.add_entry).grid(row=1, column=1, pady=5, sticky=tk.W)
        ttk.Button(self.main_frame, text="Load File", command=self.load_file).grid(row=1, column=2, pady=5, sticky=tk.W)
        
        # Search
        self.search_var = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.search_var).grid(row=2, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(self.main_frame, text="Search", command=self.search).grid(row=2, column=2, pady=5, sticky=tk.W)
        
        # Configure main_frame to expand treeview
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
        # Track tree state
        self.is_tree_open = True
        self.update_treeview()
    
    def load_tree(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            self.convert_entries(data)
            return data
        return {}
    
    def convert_entries(self, node):
        for key, val in list(node.items()):
            if isinstance(val, str):
                node[key] = {"content": val, "image": None}
            elif isinstance(val, dict) and 'content' not in val:
                self.convert_entries(val)
    
    def save_tree(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.tree_data, f, indent=4)
    
    def get_open_state(self, parent=''):
        open_state = {}
        for item in self.treeview.get_children(parent):
            text = self.treeview.item(item)['text']
            if text.endswith('/'):
                open_state[text[:-1]] = self.treeview.item(item)['open']
                open_state.update(self.get_open_state(item))
        return open_state
    
    def restore_open_state(self, open_state, parent='', data=None):
        if data is None:
            data = self.tree_data
        for name in data:
            item_id = None
            for item in self.treeview.get_children(parent):
                if self.treeview.item(item)['text'] == f"{name}/":
                    item_id = item
                    break
            if item_id and name in open_state:
                self.treeview.item(item_id, open=open_state[name])
                if isinstance(data[name], dict) and 'content' not in data[name]:
                    self.restore_open_state(open_state, item_id, data[name])
    
    def update_treeview(self, parent='', data=None):
        if data is None:
            data = self.tree_data
        # Save open state
        open_state = self.get_open_state()
        self.treeview.delete(*self.treeview.get_children(parent))
        for name, value in sorted(data.items()):
            if isinstance(value, dict):
                if 'content' in value:
                    content = value['content']
                    self.treeview.insert(parent, 'end', text=name, values=(content,))
                else:
                    node_id = self.treeview.insert(parent, 'end', text=f"{name}/", values=("",))
                    self.update_treeview(node_id, value)
        # Restore open state
        self.restore_open_state(open_state)
    
    def toggle_tree(self, event=None):
        self.is_tree_open = not self.is_tree_open
        def set_tree_state(parent='', state=None):
            for item in self.treeview.get_children(parent):
                if self.treeview.item(item)['text'].endswith('/'):
                    self.treeview.item(item, open=state)
                    set_tree_state(item, state)
        set_tree_state(state=self.is_tree_open)
    
    def get_folder_paths(self, node=None, path='', paths=None):
        if paths is None:
            paths = []
        if node is None:
            node = self.tree_data
        for name, value in node.items():
            full_path = f"{path}/{name}" if path else name
            if isinstance(value, dict) and 'content' not in value:
                paths.append(full_path)
                self.get_folder_paths(value, full_path, paths)
        return sorted(paths)
    
    def get_item_path(self, item):
        path = []
        while item:
            text = self.treeview.item(item)['text']
            if text.endswith('/'):
                text = text[:-1]
            path.append(text)
            item = self.treeview.parent(item)
        return '/'.join(reversed(path))
    
    def add_folder(self, parent_path=''):
        def submit_folder(event=None):
            path = folder_var.get().strip()
            if not path:
                messagebox.showerror("Error", "Folder path cannot be empty.")
                return
            full_path = f"{parent_path}/{path}" if parent_path else path
            parts = full_path.strip('/').split('/')
            current = self.tree_data
            for part in parts:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict) or 'content' in current[part]:
                    messagebox.showerror("Error", f"'{part}' is an entry, cannot add folder inside it.")
                    return
                current = current[part]
            self.save_tree()
            self.update_treeview()
            folder_window.destroy()
        
        folder_window = Toplevel(self.root)
        folder_window.title("Add Folder")
        ttk.Label(folder_window, text="Folder Path (e.g., subfolder):").grid(row=0, column=0, padx=5, pady=5)
        folder_var = tk.StringVar(value=parent_path)
        ttk.Entry(folder_window, textvariable=folder_var).grid(row=0, column=1, padx=5, pady=5)
        folder_window.bind('<Return>', submit_folder)
        ttk.Button(folder_window, text="Submit", command=submit_folder).grid(row=1, column=0, columnspan=2, pady=5)
    
    def add_entry(self, parent_path=''):
        image_b64 = [None]
        image_status_var = tk.StringVar(value="No image selected")
        
        def select_image():
            file = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
            if file:
                with open(file, 'rb') as f:
                    image_b64[0] = base64.b64encode(f.read()).decode('utf-8')
                image_status_var.set(f"Image selected: {os.path.basename(file)}")
        
        def submit_entry(event=None):
            folder = folder_var.get()
            name = entry_name_var.get().strip()
            content = content_var.get().strip()
            if not name or not content:
                messagebox.showerror("Error", "Entry name and content cannot be empty.")
                return
            path = f"{folder}/{name}" if folder else name
            parts = path.strip('/').split('/')
            name = parts.pop()
            current = self.tree_data
            for part in parts:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict) or 'content' in current[part]:
                    messagebox.showerror("Error", f"'{part}' is an entry, cannot traverse into it.")
                    return
                current = current[part]
            if name in current:
                if isinstance(current[name], dict) and 'content' not in current[name]:
                    messagebox.showerror("Error", f"'{name}' is a folder, cannot overwrite with entry.")
                    return
            entry_data = {"content": content}
            if image_b64[0]:
                entry_data["image"] = image_b64[0]
            current[name] = entry_data
            self.save_tree()
            self.update_treeview()
            entry_window.destroy()
        
        entry_window = Toplevel(self.root)
        entry_window.title("Add Entry")
        ttk.Label(entry_window, text="Parent Folder:").grid(row=0, column=0, padx=5, pady=5)
        folder_var = tk.StringVar(value=parent_path)
        folders = [''] + self.get_folder_paths()
        ttk.Combobox(entry_window, textvariable=folder_var, values=folders, state='readonly').grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(entry_window, text="Entry Name:").grid(row=1, column=0, padx=5, pady=5)
        entry_name_var = tk.StringVar()
        ttk.Entry(entry_window, textvariable=entry_name_var).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(entry_window, text="Content:").grid(row=2, column=0, padx=5, pady=5)
        content_var = tk.StringVar()
        ttk.Entry(entry_window, textvariable=content_var).grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(entry_window, text="Image:").grid(row=3, column=0, padx=5, pady=5)
        ttk.Label(entry_window, textvariable=image_status_var).grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(entry_window, text="Select Image", command=select_image).grid(row=4, column=0, pady=5)
        entry_window.bind('<Return>', submit_entry)
        ttk.Button(entry_window, text="Submit", command=submit_entry).grid(row=5, column=0, columnspan=2, pady=5)
    
    def edit_entry(self, item):
        path = self.get_item_path(item)
        parts = path.split('/')
        name = parts.pop()
        current = self.tree_data
        for part in parts:
            current = current[part]
        value = current[name]
        content = value['content']
        image_b64 = [value.get('image')]
        has_image = image_b64[0] is not None
        image_status_var = tk.StringVar(value="Image attached" if has_image else "No image")
        
        def select_image():
            file = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
            if file:
                with open(file, 'rb') as f:
                    image_b64[0] = base64.b64encode(f.read()).decode('utf-8')
                image_status_var.set(f"New image selected: {os.path.basename(file)}")
        
        def remove_image():
            image_b64[0] = None
            image_status_var.set("No image")
        
        def submit_edit(event=None):
            new_content = content_var.get().strip()
            if not new_content:
                messagebox.showerror("Error", "Content cannot be empty.")
                return
            value['content'] = new_content
            if image_b64[0] is None:
                value.pop('image', None)
            else:
                value['image'] = image_b64[0]
            self.save_tree()
            self.update_treeview()
            edit_window.destroy()
        
        edit_window = Toplevel(self.root)
        edit_window.title(f"Edit Entry: {path}")
        ttk.Label(edit_window, text="Content:").grid(row=0, column=0, padx=5, pady=5)
        content_var = tk.StringVar(value=content)
        ttk.Entry(edit_window, textvariable=content_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(edit_window, text="Image:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Label(edit_window, textvariable=image_status_var).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(edit_window, text="Select New Image", command=select_image).grid(row=2, column=0, pady=5)
        if has_image:
            ttk.Button(edit_window, text="Remove Image", command=remove_image).grid(row=2, column=1, pady=5)
        edit_window.bind('<Return>', submit_edit)
        ttk.Button(edit_window, text="Submit", command=submit_edit).grid(row=3, column=0, columnspan=2, pady=5)
    
    def delete_item(self, item):
        path = self.get_item_path(item)
        item_type = "folder" if self.treeview.item(item)['values'][0] == '' else "entry"
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this {item_type} (and all contents if a folder)?"):
            parts = path.split('/')
            name = parts.pop()
            current = self.tree_data
            for part in parts:
                current = current[part]
            del current[name]
            self.save_tree()
            self.update_treeview()
    
    def on_right_click(self, event):
        item = self.treeview.identify_row(event.y)
        parent_path = ''
        if item:
            self.treeview.selection_set(item)
            parent_path = self.get_item_path(item)
            if self.treeview.item(item)['values'][0] != '':  # Is entry
                menu = tk.Menu(self.root, tearoff=0)
                menu.add_command(label="Edit", command=lambda: self.edit_entry(item))
                menu.add_command(label="Delete", command=lambda: self.delete_item(item))
                menu.post(event.x_root, event.y_root)
                return
        else:
            self.treeview.selection_set('')  # Clear selection for root
        # Show folder menu (for folder or root)
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Add New Folder", command=lambda: self.add_folder(parent_path))
        menu.add_command(label="Add New Entry", command=lambda: self.add_entry(parent_path))
        if item:  # Add Delete only if clicking on a folder
            menu.add_command(label="Delete", command=lambda: self.delete_item(item))
        menu.post(event.x_root, event.y_root)
    
    def view_entry(self, event):
        item = self.treeview.focus()
        if item and self.treeview.item(item)['values'][0] != '':  # Is entry
            path = self.get_item_path(item)
            parts = path.split('/')
            name = parts.pop()
            current = self.tree_data
            for part in parts:
                current = current[part]
            value = current[name]
            content = value['content']
            image_b64 = value.get('image')
            
            viewer = Toplevel(self.root)
            viewer.title(f"Entry: {path}")
            ttk.Label(viewer, text="Content:").pack(padx=5, pady=5)
            ttk.Label(viewer, text=content).pack(padx=5, pady=5)
            if image_b64:
                try:
                    img_data = base64.b64decode(image_b64)
                    img = Image.open(BytesIO(img_data))
                    photo = ImageTk.PhotoImage(img)
                    img_label = ttk.Label(viewer, image=photo)
                    img_label.image = photo
                    img_label.pack(padx=5, pady=5)
                except Exception as e:
                    ttk.Label(viewer, text=f"Error loading image: {str(e)}").pack(padx=5, pady=5)
    
    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            self.data_file = file_path
            self.tree_data = self.load_tree(file_path)
            self.update_treeview()
            self.root.title(f"DataTree - {os.path.basename(file_path)}")
    
    def search(self):
        term = self.search_var.get().strip()
        if not term:
            messagebox.showerror("Error", "Search term cannot be empty.")
            return
        results = []
        def search_recursive(node, term, path=''):
            for name, value in sorted(node.items()):
                full_path = f"{path}/{name}" if path else name
                if term.lower() in name.lower():
                    if isinstance(value, dict):
                        if 'content' in value:
                            results.append(f"Entry: {full_path} (content: {value['content']})")
                        else:
                            results.append(f"Folder: {full_path}/")
                if isinstance(value, dict) and 'content' not in value:
                    search_recursive(value, term, full_path)
        
        search_recursive(self.tree_data, term)
        result_window = Toplevel(self.root)
        result_window.title("Search Results")
        result_text = tk.Text(result_window, height=10, width=50)
        result_text.grid(row=0, column=0, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(result_window, orient=tk.VERTICAL, command=result_text.yview)
        result_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        if results:
            for res in results:
                result_text.insert(tk.END, res + '\n')
        else:
            result_text.insert(tk.END, "No matches found.")
        result_text.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = DataTreeApp(root)
    root.mainloop()