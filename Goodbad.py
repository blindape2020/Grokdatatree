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

class DualDataTreeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dual DataTree")
        self.good_file = 'good_datatree.json'
        self.bad_file = 'bad_datatree.json'
        self.good_tree_data = self.load_tree(self.good_file)
        self.bad_tree_data = self.load_tree(self.bad_file)
        
        # Maximize window
        self.root.state('zoomed')
        
        # Main Frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Dual Panels
        self.good_frame = ttk.LabelFrame(self.main_frame, text="Good Tree", padding="5")
        self.good_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        self.bad_frame = ttk.LabelFrame(self.main_frame, text="Bad Tree", padding="5")
        self.bad_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Configure main_frame to split space evenly
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
        # Good Tree Setup
        self.good_treeview = ttk.Treeview(self.good_frame, columns=("Content",), show="tree")
        self.good_treeview.column("Content", width=200, stretch=True)
        self.good_treeview.heading("Content", text="Content")
        self.good_treeview.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        good_scrollbar = ttk.Scrollbar(self.good_frame, orient=tk.VERTICAL, command=self.good_treeview.yview)
        self.good_treeview.configure(yscroll=good_scrollbar.set)
        good_scrollbar.grid(row=0, column=3, sticky=(tk.N, tk.S))
        self.good_treeview.bind("<Double-Button-1>", lambda e: self.view_entry(e, "good"))
        self.good_treeview.bind("<Button-3>", lambda e: self.on_right_click(e, "good"))
        self.good_treeview.bind("<space>", lambda e: self.toggle_tree("good"))
        
        ttk.Button(self.good_frame, text="Add Good Folder", command=lambda: self.add_folder("good")).grid(row=1, column=0, pady=5, sticky=tk.W)
        ttk.Button(self.good_frame, text="Add Good Entry", command=lambda: self.add_entry("good")).grid(row=1, column=1, pady=5, sticky=tk.W)
        ttk.Button(self.good_frame, text="Load Good File", command=lambda: self.load_file("good")).grid(row=1, column=2, pady=5, sticky=tk.W)
        self.good_search_var = tk.StringVar()
        ttk.Entry(self.good_frame, textvariable=self.good_search_var).grid(row=2, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(self.good_frame, text="Search Good", command=lambda: self.search("good")).grid(row=2, column=2, pady=5, sticky=tk.W)
        
        self.good_frame.columnconfigure(0, weight=1)
        self.good_frame.rowconfigure(0, weight=1)
        
        # Bad Tree Setup
        self.bad_treeview = ttk.Treeview(self.bad_frame, columns=("Content",), show="tree")
        self.bad_treeview.column("Content", width=200, stretch=True)
        self.bad_treeview.heading("Content", text="Content")
        self.bad_treeview.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        bad_scrollbar = ttk.Scrollbar(self.bad_frame, orient=tk.VERTICAL, command=self.bad_treeview.yview)
        self.bad_treeview.configure(yscroll=bad_scrollbar.set)
        bad_scrollbar.grid(row=0, column=3, sticky=(tk.N, tk.S))
        self.bad_treeview.bind("<Double-Button-1>", lambda e: self.view_entry(e, "bad"))
        self.bad_treeview.bind("<Button-3>", lambda e: self.on_right_click(e, "bad"))
        self.bad_treeview.bind("<space>", lambda e: self.toggle_tree("bad"))
        
        ttk.Button(self.bad_frame, text="Add Bad Folder", command=lambda: self.add_folder("bad")).grid(row=1, column=0, pady=5, sticky=tk.W)
        ttk.Button(self.bad_frame, text="Add Bad Entry", command=lambda: self.add_entry("bad")).grid(row=1, column=1, pady=5, sticky=tk.W)
        ttk.Button(self.bad_frame, text="Load Bad File", command=lambda: self.load_file("bad")).grid(row=1, column=2, pady=5, sticky=tk.W)
        self.bad_search_var = tk.StringVar()
        ttk.Entry(self.bad_frame, textvariable=self.bad_search_var).grid(row=2, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(self.bad_frame, text="Search Bad", command=lambda: self.search("bad")).grid(row=2, column=2, pady=5, sticky=tk.W)
        
        self.bad_frame.columnconfigure(0, weight=1)
        self.bad_frame.rowconfigure(0, weight=1)
        
        # Track tree states
        self.good_tree_open = True
        self.bad_tree_open = True
        self.update_treeview("good")
        self.update_treeview("bad")
    
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
    
    def save_tree(self, tree_type):
        file_path = self.good_file if tree_type == "good" else self.bad_file
        tree_data = self.good_tree_data if tree_type == "good" else self.bad_tree_data
        with open(file_path, 'w') as f:
            json.dump(tree_data, f, indent=4)
    
    def get_open_state(self, treeview, parent=''):
        open_state = {}
        for item in treeview.get_children(parent):
            text = treeview.item(item)['text']
            if text.endswith('/'):
                open_state[text[:-1]] = treeview.item(item)['open']
                open_state.update(self.get_open_state(treeview, item))
        return open_state
    
    def restore_open_state(self, treeview, open_state, parent='', data=None):
        if data is None:
            data = self.good_tree_data if treeview == self.good_treeview else self.bad_tree_data
        for name in data:
            item_id = None
            for item in treeview.get_children(parent):
                if treeview.item(item)['text'] == f"{name}/":
                    item_id = item
                    break
            if item_id and name in open_state:
                treeview.item(item_id, open=open_state[name])
                if isinstance(data[name], dict) and 'content' not in data[name]:
                    self.restore_open_state(treeview, open_state, item_id, data[name])
    
    def update_treeview(self, tree_type, parent='', data=None):
        treeview = self.good_treeview if tree_type == "good" else self.bad_treeview
        if data is None:
            data = self.good_tree_data if tree_type == "good" else self.bad_tree_data
        open_state = self.get_open_state(treeview)
        treeview.delete(*treeview.get_children(parent))
        for name, value in sorted(data.items()):
            if isinstance(value, dict):
                if 'content' in value:
                    content = value['content']
                    treeview.insert(parent, 'end', text=name, values=(content,))
                else:
                    node_id = treeview.insert(parent, 'end', text=f"{name}/", values=("",))
                    self.update_treeview(tree_type, node_id, value)
        self.restore_open_state(treeview, open_state)
    
    def toggle_tree(self, tree_type):
        treeview = self.good_treeview if tree_type == "good" else self.bad_treeview
        is_open = self.good_tree_open if tree_type == "good" else self.bad_tree_open
        is_open = not is_open
        if tree_type == "good":
            self.good_tree_open = is_open
        else:
            self.bad_tree_open = is_open
        def set_tree_state(parent='', state=is_open):
            for item in treeview.get_children(parent):
                if treeview.item(item)['text'].endswith('/'):
                    treeview.item(item, open=state)
                    set_tree_state(item, state)
        set_tree_state()
    
    def get_folder_paths(self, tree_type, node=None, path='', paths=None):
        if paths is None:
            paths = []
        if node is None:
            node = self.good_tree_data if tree_type == "good" else self.bad_tree_data
        for name, value in node.items():
            full_path = f"{path}/{name}" if path else name
            if isinstance(value, dict) and 'content' not in value:
                paths.append(full_path)
                self.get_folder_paths(tree_type, value, full_path, paths)
        return sorted(paths)
    
    def get_item_path(self, treeview, item):
        path = []
        while item:
            text = treeview.item(item)['text']
            if text.endswith('/'):
                text = text[:-1]
            path.append(text)
            item = treeview.parent(item)
        return '/'.join(reversed(path))
    
    def add_folder(self, tree_type, parent_path=''):
        def submit_folder(event=None):
            path = folder_var.get().strip()
            if not path:
                messagebox.showerror("Error", "Folder path cannot be empty.")
                return
            full_path = f"{parent_path}/{path}" if parent_path else path
            parts = full_path.strip('/').split('/')
            tree_data = self.good_tree_data if tree_type == "good" else self.bad_tree_data
            current = tree_data
            for part in parts:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict) or 'content' in current[part]:
                    messagebox.showerror("Error", f"'{part}' is an entry, cannot add folder inside it.")
                    return
                current = current[part]
            self.save_tree(tree_type)
            self.update_treeview(tree_type)
            folder_window.destroy()
        
        folder_window = Toplevel(self.root)
        folder_window.title(f"Add {'Good' if tree_type == 'good' else 'Bad'} Folder")
        ttk.Label(folder_window, text="Folder Path (e.g., subfolder):").grid(row=0, column=0, padx=5, pady=5)
        folder_var = tk.StringVar(value=parent_path)
        ttk.Entry(folder_window, textvariable=folder_var).grid(row=0, column=1, padx=5, pady=5)
        folder_window.bind('<Return>', submit_folder)
        ttk.Button(folder_window, text="Submit", command=submit_folder).grid(row=1, column=0, columnspan=2, pady=5)
    
    def add_entry(self, tree_type, parent_path=''):
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
            tree_data = self.good_tree_data if tree_type == "good" else self.bad_tree_data
            current = tree_data
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
            self.save_tree(tree_type)
            self.update_treeview(tree_type)
            entry_window.destroy()
        
        entry_window = Toplevel(self.root)
        entry_window.title(f"Add {'Good' if tree_type == 'good' else 'Bad'} Entry")
        ttk.Label(entry_window, text="Parent Folder:").grid(row=0, column=0, padx=5, pady=5)
        folder_var = tk.StringVar(value=parent_path)
        folders = [''] + self.get_folder_paths(tree_type)
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
    
    def edit_entry(self, tree_type, item):
        treeview = self.good_treeview if tree_type == "good" else self.bad_treeview
        tree_data = self.good_tree_data if tree_type == "good" else self.bad_tree_data
        path = self.get_item_path(treeview, item)
        parts = path.split('/')
        name = parts.pop()
        current = tree_data
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
            self.save_tree(tree_type)
            self.update_treeview(tree_type)
            edit_window.destroy()
        
        edit_window = Toplevel(self.root)
        edit_window.title(f"Edit {'Good' if tree_type == 'good' else 'Bad'} Entry: {path}")
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
    
    def delete_item(self, tree_type, item):
        treeview = self.good_treeview if tree_type == "good" else self.bad_treeview
        tree_data = self.good_tree_data if tree_type == "good" else self.bad_tree_data
        path = self.get_item_path(treeview, item)
        item_type = "folder" if treeview.item(item)['values'][0] == '' else "entry"
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this {item_type} (and all contents if a folder)?"):
            parts = path.split('/')
            name = parts.pop()
            current = tree_data
            for part in parts:
                current = current[part]
            del current[name]
            self.save_tree(tree_type)
            self.update_treeview(tree_type)
    
    def on_right_click(self, event, tree_type):
        treeview = self.good_treeview if tree_type == "good" else self.bad_treeview
        item = treeview.identify_row(event.y)
        parent_path = ''
        if item:
            treeview.selection_set(item)
            parent_path = self.get_item_path(treeview, item)
            if treeview.item(item)['values'][0] != '':  # Is entry
                menu = tk.Menu(self.root, tearoff=0)
                menu.add_command(label="Edit", command=lambda: self.edit_entry(tree_type, item))
                menu.add_command(label="Delete", command=lambda: self.delete_item(tree_type, item))
                menu.post(event.x_root, event.y_root)
                return
        else:
            treeview.selection_set('')
        # Show folder menu (for folder or root)
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label=f"Add New {'Good' if tree_type == 'good' else 'Bad'} Folder", command=lambda: self.add_folder(tree_type, parent_path))
        menu.add_command(label=f"Add New {'Good' if tree_type == 'good' else 'Bad'} Entry", command=lambda: self.add_entry(tree_type, parent_path))
        if item:  # Add Delete only if clicking on a folder
            menu.add_command(label="Delete", command=lambda: self.delete_item(tree_type, item))
        menu.post(event.x_root, event.y_root)
    
    def view_entry(self, event, tree_type):
        treeview = self.good_treeview if tree_type == "good" else self.bad_treeview
        tree_data = self.good_tree_data if tree_type == "good" else self.bad_tree_data
        item = treeview.focus()
        if item and treeview.item(item)['values'][0] != '':
            path = self.get_item_path(treeview, item)
            parts = path.split('/')
            name = parts.pop()
            current = tree_data
            for part in parts:
                current = current[part]
            value = current[name]
            content = value['content']
            image_b64 = value.get('image')
            
            viewer = Toplevel(self.root)
            viewer.title(f"{'Good' if tree_type == 'good' else 'Bad'} Entry: {path}")
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
    
    def load_file(self, tree_type):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            if tree_type == "good":
                self.good_file = file_path
                self.good_tree_data = self.load_tree(file_path)
                self.update_treeview("good")
                self.good_frame.config(text=f"Good Tree - {os.path.basename(file_path)}")
            else:
                self.bad_file = file_path
                self.bad_tree_data = self.load_tree(file_path)
                self.update_treeview("bad")
                self.bad_frame.config(text=f"Bad Tree - {os.path.basename(file_path)}")
    
    def search(self, tree_type):
        search_var = self.good_search_var if tree_type == "good" else self.bad_search_var
        tree_data = self.good_tree_data if tree_type == "good" else self.bad_tree_data
        term = search_var.get().strip()
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
        
        search_recursive(tree_data, term)
        result_window = Toplevel(self.root)
        result_window.title(f"{'Good' if tree_type == 'good' else 'Bad'} Search Results")
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
    app = DualDataTreeApp(root)
    root.mainloop()