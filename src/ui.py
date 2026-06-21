from pathlib import Path
import customtkinter as ctk
from datetime import datetime
from tkinter import filedialog, messagebox, colorchooser
import webbrowser
from settings_manager import (
    get_archive_root,
    set_archive_root,
    clear_archive_root,
    get_conversation_ui_settings,
)
from conversation_converter import apply_ui_patch_to_folder
from updater import update_conversation_index, update_menu_index
from search_engine import search_archive
from folder_manager import build_archive, normalize_folder_names, create_archive_folder, parse_years
from conversation_style_manager import (
    save_and_generate_conversation_ui_patch,
    reset_conversation_ui_patch,
    image_file_to_data_uri,
)




APP_NAME = "Archive Builder"
APP_VERSION = "v0.0.9"

REPO_ROOT = Path(__file__).resolve().parents[1]


COLORS = {
    "window": "#12111f",
    "sidebar": "#0e0d1a",
    "panel": "#1a1830",
    "panel_hover": "#221f3d",
    "panel_active": "#1d1b38",
    "border": "#2a2840",
    "border_active": "#534AB7",
    "text": "#c9b8f4",
    "text_soft": "#7a7a9e",
    "text_muted": "#4a4870",
    "label": "#3d3b5e",
    "purple": "#534AB7",
    "purple_dark": "#26215C",
    "purple_light": "#9d8ef4",
    "teal_dark": "#04342C",
    "teal": "#5DCAA5",
    "amber_dark": "#412402",
    "amber": "#EF9F27",
    "blue_dark": "#042C53",
    "blue": "#85B7EB",
    "red_dark": "#501313",
    "red": "#f09595",
    "gray_icon": "#1e1c35",
}


class ArchiveBuilderUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ChatGPT Archive Builder")
        self.geometry("920x560")
        self.minsize(820, 500)

        ctk.set_appearance_mode("dark")

        self.configure(fg_color=COLORS["window"])

        self.current_panel = "new_archive"
        self.saved_archive_root = get_archive_root()

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_area()

        self.show_panel("new_archive")

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=210,
            corner_radius=0,
            fg_color=COLORS["sidebar"],
            border_width=1,
            border_color=COLORS["border"],
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.sidebar.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=14, pady=(16, 12))

        icon = ctk.CTkLabel(
            top,
            text="▣",
            width=32,
            height=32,
            corner_radius=8,
            fg_color=COLORS["purple"],
            text_color="#ffffff",
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        icon.pack(anchor="w", pady=(0, 8))

        app_name = ctk.CTkLabel(
            top,
            text=APP_NAME,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        app_name.pack(anchor="w")

        app_sub = ctk.CTkLabel(
            top,
            text=APP_VERSION,
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(size=11),
        )
        app_sub.pack(anchor="w", pady=(1, 0))

        self.build_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.build_section.grid(row=1, column=0, sticky="ew", padx=10, pady=(8, 0))

        self.add_sidebar_label(self.build_section, "Build")

        self.nav_buttons = {}

        self.add_nav_button(self.build_section, "new_archive", "+  New archive")
        self.add_nav_button(self.build_section, "add_folder", "📁  Add folder")
        self.add_nav_button(self.build_section, "update_folder", "↻  Update folder")

        self.manage_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.manage_section.grid(row=2, column=0, sticky="new", padx=10, pady=(14, 0))

        self.add_sidebar_label(self.manage_section, "Manage")

        self.add_nav_button(self.manage_section, "search_archive", "⌕  Search archive")
        self.add_nav_button(self.manage_section, "customize_ui", "⚙  Customize UI")
        self.add_nav_button(self.manage_section, "show_root", "⌾  Show root")
        self.add_nav_button(self.manage_section, "clear_root", "🗑  Clear root", danger=True)

        bottom = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
        )
        bottom.grid(row=3, column=0, sticky="ew", padx=10, pady=10)

        open_button = ctk.CTkButton(
            bottom,
            text="↗  Open archive",
            height=40,
            fg_color=COLORS["purple"],
            hover_color="#3d3489",
            text_color="#e8e4ff",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.open_archive_from_ui,
        )
        open_button.pack(fill="x", padx=0, pady=0)

    def panel_show_root(self):
        self.panel_header("Saved archive root")

        box = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=10,
        )
        box.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        box.grid_columnconfigure(0, weight=1)
        box.grid_columnconfigure(1, weight=1)
        box.grid_columnconfigure(2, weight=1)

        title = ctk.CTkLabel(
            box,
            text="Saved archive root",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(18, 4))

        current_root = self.saved_archive_root or get_archive_root()
        self.saved_archive_root = current_root

        root_text = str(current_root) if current_root else "No archive root saved yet."

        self.show_root_value_var = ctk.StringVar(value=root_text)

        root_entry = ctk.CTkEntry(
            box,
            textvariable=self.show_root_value_var,
            height=38,
            fg_color=COLORS["window"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        root_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=18, pady=(10, 14))

        copy_button = ctk.CTkButton(
            box,
            text="Copy path",
            height=38,
            fg_color=COLORS["panel_active"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["text"],
            command=self.copy_saved_root_to_clipboard,
        )
        copy_button.grid(row=2, column=0, sticky="ew", padx=(18, 6), pady=(0, 18))

        set_button = ctk.CTkButton(
            box,
            text="Browse and save root",
            height=38,
            fg_color=COLORS["purple"],
            hover_color="#3d3489",
            text_color="#e8e4ff",
            command=self.browse_and_save_archive_root,
        )
        set_button.grid(row=2, column=1, sticky="ew", padx=6, pady=(0, 18))

        open_button = ctk.CTkButton(
            box,
            text="↗  Open archive",
            height=38,
            fg_color=COLORS["panel_active"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["text"],
            command=self.open_archive_from_ui,
        )
        open_button.grid(row=2, column=2, sticky="ew", padx=(6, 18), pady=(0, 18))


    def panel_clear_root(self):
        self.panel_header("Clear saved root")

        box = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=10,
        )
        box.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        box.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            box,
            text="Clear saved archive root",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=18, pady=(18, 4))

        message = ctk.CTkLabel(
            box,
            text="This will remove the saved archive root from local settings. It will not delete your archive files.",
            text_color=COLORS["text_soft"],
            font=ctk.CTkFont(size=13),
            wraplength=620,
            justify="left",
        )
        message.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 18))

        clear_button = ctk.CTkButton(
            box,
            text="🗑  Clear saved root",
            height=42,
            fg_color=COLORS["red_dark"],
            hover_color="#6a1a1a",
            text_color=COLORS["red"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.clear_saved_root_from_ui,
        )
        clear_button.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))


    def copy_saved_root_to_clipboard(self):
        current_root = self.saved_archive_root or get_archive_root()

        if not current_root:
            messagebox.showwarning(
                "No saved root",
                "There is no saved archive root to copy."
            )
            self.set_status("no saved root to copy.")
            return

        self.clipboard_clear()
        self.clipboard_append(str(current_root))
        self.set_status("saved root copied to clipboard.")

    def browse_and_save_archive_root(self):
        folder = filedialog.askdirectory(
            title="Choose archive root"
        )

        if not folder:
            self.set_status("set root cancelled.")
            return

        archive_root = Path(folder)
        index_path = archive_root / "index.html"

        if not index_path.exists():
            confirm = messagebox.askyesno(
                "No archive homepage found",
                f"No index.html was found in:\n\n{archive_root}\n\n"
                "Save this folder as the archive root anyway?"
            )

            if not confirm:
                self.set_status("set root cancelled: no index.html found.")
                return

        set_archive_root(archive_root)
        self.saved_archive_root = archive_root

        if hasattr(self, "show_root_value_var"):
            self.show_root_value_var.set(str(archive_root))

        messagebox.showinfo(
            "Archive root saved",
            f"Saved archive root:\n\n{archive_root}"
        )

        self.set_status("archive root saved.")


    def clear_saved_root_from_ui(self):
        confirm = messagebox.askyesno(
            "Clear saved root",
            "Clear the saved archive root?\n\nThis will not delete any archive files."
        )

        if not confirm:
            self.set_status("clear saved root cancelled.")
            return

        clear_archive_root()
        self.saved_archive_root = None

        messagebox.showinfo(
            "Saved root cleared",
            "The saved archive root was cleared."
        )

        self.set_status("saved root cleared.")
        self.show_panel("show_root")


    def open_archive_from_ui(self):
        current_root = self.saved_archive_root or get_archive_root()

        if not current_root:
            messagebox.showwarning(
                "No saved root",
                "No archive root is saved yet."
            )
            self.set_status("cannot open archive: no saved root.")
            return

        index_path = Path(current_root) / "index.html"

        if not index_path.exists():
            messagebox.showerror(
                "Archive homepage not found",
                f"Could not find:\n\n{index_path}"
            )
            self.set_status("cannot open archive: index.html not found.")
            return

        webbrowser.open(index_path.resolve().as_uri())
        self.set_status("archive opened in browser.")

    def panel_search_archive(self):
        self.panel_header("Search archive")

        form = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=10,
        )
        form.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        form.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            form,
            text="Search your archive",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(18, 4))

        subtitle = ctk.CTkLabel(
            form,
            text="Search exported conversation files by one or multiple keywords. Multiple keywords are separated by commas or semicolons, and all keywords must be present in the conversation.",
            text_color=COLORS["text_soft"],
            font=ctk.CTkFont(size=13),
            wraplength=620,
            justify="left",
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 18))

        root_label = ctk.CTkLabel(
            form,
            text="Archive or folder to search",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        root_label.grid(row=2, column=0, sticky="w", padx=18, pady=(0, 6))

        self.search_root_var = ctk.StringVar(
            value=str(self.saved_archive_root) if self.saved_archive_root else ""
        )

        root_entry = ctk.CTkEntry(
            form,
            textvariable=self.search_root_var,
            height=38,
            fg_color=COLORS["window"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text="Choose archive root or any folder inside it",
            placeholder_text_color=COLORS["text_muted"],
        )
        root_entry.grid(row=3, column=0, sticky="ew", padx=(18, 8), pady=(0, 14))

        browse_button = ctk.CTkButton(
            form,
            text="Browse",
            width=90,
            height=38,
            fg_color=COLORS["purple"],
            hover_color="#3d3489",
            text_color="#e8e4ff",
            command=self.browse_search_root,
        )
        browse_button.grid(row=3, column=1, sticky="e", padx=(0, 18), pady=(0, 14))

        keywords_label = ctk.CTkLabel(
            form,
            text="Keyword(s)",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        keywords_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 6))

        self.search_keywords_var = ctk.StringVar()

        keywords_entry = ctk.CTkEntry(
            form,
            textvariable=self.search_keywords_var,
            height=38,
            fg_color=COLORS["window"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text="Example: Connor, Jericho, dream",
            placeholder_text_color=COLORS["text_muted"],
        )
        keywords_entry.grid(row=5, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 18))

        search_button = ctk.CTkButton(
            form,
            text="⌕  Search archive",
            height=42,
            fg_color=COLORS["teal_dark"],
            hover_color="#075244",
            text_color=COLORS["teal"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.search_archive_from_ui,
        )
        search_button.grid(row=6, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 18))

        results_frame = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=10,
        )
        results_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 14))
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)

        results_title = ctk.CTkLabel(
            results_frame,
            text="Results",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        results_title.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 8))

        self.search_results_area = ctk.CTkScrollableFrame(
            results_frame,
            fg_color=COLORS["window"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
            height=190,
        )
        self.search_results_area.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self.search_results_area.grid_columnconfigure(0, weight=1)

        empty_label = ctk.CTkLabel(
            self.search_results_area,
            text="No search performed yet.",
            text_color=COLORS["text_soft"],
            font=ctk.CTkFont(size=12),
        )
        empty_label.grid(row=0, column=0, sticky="w", padx=12, pady=12)


    def browse_search_root(self):
        initial_dir = (
            str(self.saved_archive_root)
            if self.saved_archive_root and self.saved_archive_root.exists()
            else None
        )

        folder = filedialog.askdirectory(
            title="Choose archive or folder to search",
            initialdir=initial_dir,
        )

        if folder:
            self.search_root_var.set(folder)
            self.set_status("search folder selected.")


    def clear_search_results_area(self):
        for widget in self.search_results_area.winfo_children():
            widget.destroy()


    def open_search_result(self, file_path):
        path = Path(file_path)

        if not path.exists():
            messagebox.showerror(
                "File not found",
                f"Could not find:\n\n{path}"
            )
            self.set_status("search result could not be opened.")
            return

        webbrowser.open(path.resolve().as_uri())
        self.set_status("search result opened.")


    def write_search_results(self, search_result: dict):
        self.clear_search_results_area()

        results = search_result["results"]

        summary = (
            f"Search complete • "
            f"{len(results)} result(s) • "
            f"{search_result['files_scanned']} file(s) scanned • "
            f"Keywords: {' | '.join(search_result['keywords'])}"
        )

        summary_label = ctk.CTkLabel(
            self.search_results_area,
            text=summary,
            text_color=COLORS["text_soft"],
            font=ctk.CTkFont(size=12),
            wraplength=900,
            justify="left",
        )
        summary_label.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))

        if not results:
            no_result_label = ctk.CTkLabel(
                self.search_results_area,
                text="No conversation found.",
                text_color=COLORS["text_soft"],
                font=ctk.CTkFont(size=12),
            )
            no_result_label.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 12))
            return

        for index, result in enumerate(results, start=1):
            card = ctk.CTkFrame(
                self.search_results_area,
                fg_color=COLORS["panel"],
                border_width=1,
                border_color=COLORS["border"],
                corner_radius=8,
            )
            card.grid(row=index, column=0, sticky="ew", padx=10, pady=5)
            card.grid_columnconfigure(0, weight=1)

            title_button = ctk.CTkButton(
                card,
                text=f"{index}. {result['title']}",
                height=32,
                anchor="w",
                fg_color="transparent",
                hover_color=COLORS["panel_hover"],
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda path=result["file_path"]: self.open_search_result(path),
            )
            title_button.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))

            path_label = ctk.CTkLabel(
                card,
                text=result["relative_path"],
                text_color=COLORS["text_muted"],
                font=ctk.CTkFont(size=11, family="Consolas"),
                wraplength=900,
                justify="left",
            )
            path_label.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))


    def search_archive_from_ui(self):
        raw_root = self.search_root_var.get().strip().strip('"')
        raw_keywords = self.search_keywords_var.get().strip()

        if not raw_root:
            messagebox.showerror(
                "Missing search folder",
                "Please choose or enter an archive/folder to search first."
            )
            self.set_status("search cancelled: no folder selected.")
            return

        if not raw_keywords:
            messagebox.showerror(
                "Missing keywords",
                "Please enter at least one keyword."
            )
            self.set_status("search cancelled: no keyword entered.")
            return

        root_path = Path(raw_root)

        try:
            search_result = search_archive(
                root_path=root_path,
                raw_keywords=raw_keywords,
            )

        except Exception as error:
            messagebox.showerror(
                "Search failed",
                str(error)
            )
            self.set_status("search failed.")
            return

        results = search_result["results"]

        self.write_search_results(search_result)

        self.set_status(f"search complete: {len(results)} result(s).")

    def panel_update_folder(self):
        self.panel_header("Update folder")

        form = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=10,
        )
        form.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        form.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            form,
            text="Update a folder",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(18, 4))

        subtitle = ctk.CTkLabel(
            form,
            text="Choose a conversation folder to patch exported chats, or a menu folder to rebuild its folder links.",
            text_color=COLORS["text_soft"],
            font=ctk.CTkFont(size=13),
            wraplength=620,
            justify="left",
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 18))

        folder_label = ctk.CTkLabel(
            form,
            text="Folder to update",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        folder_label.grid(row=2, column=0, sticky="w", padx=18, pady=(0, 6))

        self.update_folder_path_var = ctk.StringVar()

        folder_entry = ctk.CTkEntry(
            form,
            textvariable=self.update_folder_path_var,
            height=38,
            fg_color=COLORS["window"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text="Example: E:\\Archives\\Conversations\\2026\\June 2026",
            placeholder_text_color=COLORS["text_muted"],
        )
        folder_entry.grid(row=3, column=0, sticky="ew", padx=(18, 8), pady=(0, 14))

        browse_button = ctk.CTkButton(
            form,
            text="Browse",
            width=90,
            height=38,
            fg_color=COLORS["purple"],
            hover_color="#3d3489",
            text_color="#e8e4ff",
            command=self.browse_update_folder,
        )
        browse_button.grid(row=3, column=1, sticky="e", padx=(0, 18), pady=(0, 14))

        self.recursive_update_var = ctk.BooleanVar(value=False)

        recursive_checkbox = ctk.CTkCheckBox(
            form,
            text="Update this folder and all subfolders",
            variable=self.recursive_update_var,
            text_color=COLORS["text_soft"],
            fg_color=COLORS["purple"],
            hover_color="#3d3489",
            border_color=COLORS["border_active"],
        )
        recursive_checkbox.grid(row=5, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 14))

        update_button = ctk.CTkButton(
            form,
            text="↻  Update folder",
            height=42,
            fg_color=COLORS["blue_dark"],
            hover_color="#063a6d",
            text_color=COLORS["blue"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.update_folder_from_ui,
        )
        update_button.grid(row=4, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 18))

    def panel_add_folder(self):
        self.panel_header("Add folder")

        form = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=10,
        )
        form.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        form.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            form,
            text="Add a folder to an archive",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(18, 4))

        subtitle = ctk.CTkLabel(
            form,
            text="Create a new folder inside an existing archive folder. Choose Menu folder for folders that contain other folders, or Conversation folder for folders that will contain exported chats.",
            text_color=COLORS["text_soft"],
            font=ctk.CTkFont(size=13),
            wraplength=620,
            justify="left",
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 18))

        archive_root_label = ctk.CTkLabel(
            form,
            text="Archive root",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        archive_root_label.grid(row=2, column=0, sticky="w", padx=18, pady=(0, 6))

        self.add_folder_archive_root_var = ctk.StringVar(
            value=str(self.saved_archive_root) if self.saved_archive_root else ""
        )

        archive_root_entry = ctk.CTkEntry(
            form,
            textvariable=self.add_folder_archive_root_var,
            height=38,
            fg_color=COLORS["window"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text="Archive root folder",
            placeholder_text_color=COLORS["text_muted"],
        )
        archive_root_entry.grid(row=3, column=0, sticky="ew", padx=(18, 8), pady=(0, 14))

        archive_root_browse = ctk.CTkButton(
            form,
            text="Browse",
            width=90,
            height=38,
            fg_color=COLORS["purple"],
            hover_color="#3d3489",
            text_color="#e8e4ff",
            command=self.browse_add_folder_archive_root,
        )
        archive_root_browse.grid(row=3, column=1, sticky="e", padx=(0, 18), pady=(0, 14))

        parent_label = ctk.CTkLabel(
            form,
            text="Parent folder",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        parent_label.grid(row=4, column=0, sticky="w", padx=18, pady=(0, 6))

        self.add_folder_parent_var = ctk.StringVar()

        parent_entry = ctk.CTkEntry(
            form,
            textvariable=self.add_folder_parent_var,
            height=38,
            fg_color=COLORS["window"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text="Folder where the new folder will be created",
            placeholder_text_color=COLORS["text_muted"],
        )
        parent_entry.grid(row=5, column=0, sticky="ew", padx=(18, 8), pady=(0, 14))

        parent_browse = ctk.CTkButton(
            form,
            text="Browse",
            width=90,
            height=38,
            fg_color=COLORS["purple"],
            hover_color="#3d3489",
            text_color="#e8e4ff",
            command=self.browse_add_folder_parent,
        )
        parent_browse.grid(row=5, column=1, sticky="e", padx=(0, 18), pady=(0, 14))

        folder_name_label = ctk.CTkLabel(
            form,
            text="New folder name",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        folder_name_label.grid(row=6, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 6))

        self.add_folder_name_var = ctk.StringVar()

        folder_name_entry = ctk.CTkEntry(
            form,
            textvariable=self.add_folder_name_var,
            height=38,
            fg_color=COLORS["window"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text="Example: Dreams",
            placeholder_text_color=COLORS["text_muted"],
        )
        folder_name_entry.grid(row=7, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 14))

        type_label = ctk.CTkLabel(
            form,
            text="Folder type",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        type_label.grid(row=8, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 6))

        self.add_folder_type_var = ctk.StringVar(value="menu")

        type_frame = ctk.CTkFrame(form, fg_color="transparent")
        type_frame.grid(row=9, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 18))

        menu_radio = ctk.CTkRadioButton(
            type_frame,
            text="Menu folder",
            variable=self.add_folder_type_var,
            value="menu",
            text_color=COLORS["text_soft"],
            fg_color=COLORS["purple"],
            hover_color="#3d3489",
        )
        menu_radio.pack(side="left", padx=(0, 20))

        conversation_radio = ctk.CTkRadioButton(
            type_frame,
            text="Conversation folder",
            variable=self.add_folder_type_var,
            value="conversation",
            text_color=COLORS["text_soft"],
            fg_color=COLORS["purple"],
            hover_color="#3d3489",
        )
        conversation_radio.pack(side="left")

        create_button = ctk.CTkButton(
            form,
            text="📁  Create folder",
            height=42,
            fg_color=COLORS["amber_dark"],
            hover_color="#5a3204",
            text_color=COLORS["amber"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.add_folder_from_ui,
        )
        create_button.grid(row=10, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 18))


    def browse_add_folder_archive_root(self):
        folder = filedialog.askdirectory(
            title="Choose archive root"
        )

        if folder:
            self.add_folder_archive_root_var.set(folder)
            self.saved_archive_root = Path(folder)
            set_archive_root(self.saved_archive_root)
            self.set_status("archive root selected.")


    def browse_add_folder_parent(self):
        initial_dir = (
            str(self.saved_archive_root)
            if self.saved_archive_root and self.saved_archive_root.exists()
            else None
        )

        folder = filedialog.askdirectory(
            title="Choose parent folder",
            initialdir=initial_dir,
        )

        if folder:
            self.add_folder_parent_var.set(folder)
            self.set_status("parent folder selected.")


    def add_folder_from_ui(self):
        archive_root_raw = self.add_folder_archive_root_var.get().strip().strip('"')
        parent_folder_raw = self.add_folder_parent_var.get().strip().strip('"')
        folder_name = self.add_folder_name_var.get().strip()
        index_type = self.add_folder_type_var.get()

        if not archive_root_raw:
            messagebox.showerror(
                "Missing archive root",
                "Please choose or enter the archive root first."
            )
            self.set_status("folder creation cancelled: no archive root.")
            return

        if not parent_folder_raw:
            messagebox.showerror(
                "Missing parent folder",
                "Please choose or enter the parent folder first."
            )
            self.set_status("folder creation cancelled: no parent folder.")
            return

        if not folder_name:
            messagebox.showerror(
                "Missing folder name",
                "Please enter a new folder name."
            )
            self.set_status("folder creation cancelled: no folder name.")
            return

        archive_root = Path(archive_root_raw)
        parent_folder = Path(parent_folder_raw)

        try:
            result = create_archive_folder(
                archive_root=archive_root,
                parent_folder=parent_folder,
                folder_name=folder_name,
                index_type=index_type,
            )

            self.saved_archive_root = archive_root
            set_archive_root(archive_root)

        except Exception as error:
            messagebox.showerror(
                "Folder creation failed",
                str(error)
            )
            self.set_status("folder creation failed.")
            return

        parent_update = result["parent_update"]

        message = (
            f"Folder created successfully.\n\n"
            f"Folder: {result['new_folder']}\n"
            f"Index file: {result['new_index']}\n"
            f"Index type: {result['index_type']}\n\n"
            f"Parent index updated: {result['parent_index']}\n"
            f"New link added: {'yes' if parent_update['was_added'] else 'already existed'}\n"
            f"Total links in parent index: {parent_update['total_links']}"
        )

        messagebox.showinfo(
            "Folder created",
            message
        )

        self.set_status(f"folder created: {folder_name}.")


    def browse_update_folder(self):
        folder = filedialog.askdirectory(
            title="Choose conversation folder to update"
        )

        if folder:
            self.update_folder_path_var.set(folder)
            self.set_status("conversation folder selected.")

    def detect_folder_type(self, folder_path: Path) -> str:
        index_path = folder_path / "index.html"

        if not index_path.exists():
            return "none"

        index_html = index_path.read_text(encoding="utf-8", errors="ignore")

        if "Folder menu." in index_html or ">FOLDERS<" in index_html:
            return "menu"

        return "conversation"


    def update_single_folder_by_type(self, folder_path: Path) -> dict:
        folder_type = self.detect_folder_type(folder_path)

        if folder_type == "none":
            return {
                "folder_path": folder_path,
                "folder_type": "none",
                "updated": False,
                "summary": "no index.html",
            }

        if folder_type == "menu":
            result = update_menu_index(folder_path)

            return {
                "folder_path": folder_path,
                "folder_type": "menu",
                "updated": True,
                "summary": f"{result['total_folders']} folder(s) listed",
            }

        patch_result = apply_ui_patch_to_folder(folder_path)
        index_result = update_conversation_index(folder_path)

        return {
            "folder_path": folder_path,
            "folder_type": "conversation",
            "updated": True,
            "summary": (
                f"{index_result['total_links']} conversation(s), "
                f"{patch_result['changed_count']} file(s) patched"
            ),
        }


    def update_folder_tree_from_ui(self, root_folder: Path):
        if not root_folder.exists():
            messagebox.showerror(
                "Folder not found",
                f"Could not find:\n\n{root_folder}"
            )
            self.set_status("recursive update failed: folder not found.")
            return

        folders_to_update = [
            folder
            for folder in root_folder.rglob("*")
            if folder.is_dir() and (folder / "index.html").exists()
        ]

        if (root_folder / "index.html").exists():
            folders_to_update.append(root_folder)

        folders_to_update = sorted(
            set(folders_to_update),
            key=lambda path: len(path.parts),
            reverse=True,
        )

        if not folders_to_update:
            messagebox.showwarning(
                "No indexed folders found",
                "No folders with index.html were found under the selected folder."
            )
            self.set_status("recursive update cancelled: no indexed folders found.")
            return

        confirm = messagebox.askyesno(
            "Recursive update",
            f"This will update {len(folders_to_update)} indexed folder(s).\n\n"
            f"Selected folder:\n{root_folder}\n\n"
            "Continue?"
        )

        if not confirm:
            self.set_status("recursive update cancelled.")
            return

        updated_menus = 0
        updated_conversations = 0
        skipped = 0
        errors = []

        for folder_path in folders_to_update:
            try:
                result = self.update_single_folder_by_type(folder_path)

                if not result["updated"]:
                    skipped += 1
                    continue

                if result["folder_type"] == "menu":
                    updated_menus += 1

                if result["folder_type"] == "conversation":
                    updated_conversations += 1

            except Exception as error:
                errors.append(f"{folder_path}: {error}")

        message = (
            f"Recursive update complete.\n\n"
            f"Root folder:\n{root_folder}\n\n"
            f"Menu folders updated: {updated_menus}\n"
            f"Conversation folders updated: {updated_conversations}\n"
            f"Skipped folders: {skipped}\n"
            f"Errors: {len(errors)}"
        )

        if errors:
            preview_errors = "\n".join(errors[:5])
            message += f"\n\nFirst errors:\n{preview_errors}"

            if len(errors) > 5:
                message += f"\n\n...and {len(errors) - 5} more."

        messagebox.showinfo(
            "Recursive update finished",
            message
        )

        self.set_status(
            f"recursive update complete: {updated_menus} menu folder(s), "
            f"{updated_conversations} conversation folder(s)."
        )


    def update_folder_from_ui(self):
        raw_path = self.update_folder_path_var.get().strip().strip('"')

        if not raw_path:
            messagebox.showerror(
                "Missing folder",
                "Please choose or enter a conversation folder first."
            )
            self.set_status("folder update cancelled: no folder selected.")
            return

        folder_path = Path(raw_path)
        index_path = folder_path / "index.html"

        recursive_update = (
            hasattr(self, "recursive_update_var")
            and self.recursive_update_var.get()
        )

        if recursive_update:
            self.update_folder_tree_from_ui(folder_path)
            return

        is_menu_folder = False

        if index_path.exists():
            index_html = index_path.read_text(encoding="utf-8", errors="ignore")
            is_menu_folder = "Folder menu." in index_html or ">FOLDERS<" in index_html

        try:
            if is_menu_folder:
                menu_result = update_menu_index(folder_path)

                messagebox.showinfo(
                    "Menu folder updated",
                    f"Menu folder updated successfully.\n\n"
                    f"Folder: {menu_result['folder_path']}\n"
                    f"Index file: {menu_result['index_path']}\n"
                    f"Folders listed: {menu_result['total_folders']}"
                )

                self.set_status(
                    f"menu folder updated: {menu_result['total_folders']} folder(s) listed."
                )
                return

            patch_result = apply_ui_patch_to_folder(folder_path)
            index_result = update_conversation_index(folder_path)

        except Exception as error:
            messagebox.showerror(
                "Folder update failed",
                str(error)
            )
            self.set_status("folder update failed.")
            return

        message = (
            f"Folder updated successfully.\n\n"
            f"HTML conversation files found: {patch_result['total_files']}\n"
            f"Files updated with UI patch: {patch_result['changed_count']}\n"
            f"Files already up to date: {patch_result['unchanged_count']}\n\n"
            f"New conversations added to index: {index_result['added_count']}\n"
            f"Total conversations listed: {index_result['total_links']}"
        )

        messagebox.showinfo(
            "Folder updated",
            message
        )

        self.set_status(
            f"folder updated: {index_result['total_links']} conversation(s) listed."
        )

    def create_main_area(self):
        self.main = ctk.CTkFrame(
            self,
            fg_color=COLORS["window"],
            corner_radius=0,
        )
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self.topbar = ctk.CTkFrame(
            self.main,
            height=58,
            fg_color=COLORS["window"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=0,
        )
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.grid_propagate(False)
        self.topbar.grid_columnconfigure(0, weight=1)

        self.topbar_title = ctk.CTkLabel(
            self.topbar,
            text="New archive",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.topbar_title.grid(row=0, column=0, sticky="w", padx=22)


        self.content = ctk.CTkFrame(
            self.main,
            fg_color=COLORS["window"],
            corner_radius=0,
        )
        self.content.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        self.status_bar = ctk.CTkFrame(
            self.main,
            height=34,
            fg_color=COLORS["window"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=0,
        )
        self.status_bar.grid(row=2, column=0, sticky="ew")
        self.status_bar.grid_propagate(False)

        self.status_dot = ctk.CTkLabel(
            self.status_bar,
            text="●",
            text_color=COLORS["teal"],
            font=ctk.CTkFont(size=11),
        )
        self.status_dot.pack(side="left", padx=(20, 6))

        self.status_text = ctk.CTkLabel(
            self.status_bar,
            text="root: not defined — ready.",
            text_color=COLORS["label"],
            font=ctk.CTkFont(size=11, family="Consolas"),
        )
        self.status_text.pack(side="left")

    def add_sidebar_label(self, parent, text):
        label = ctk.CTkLabel(
            parent,
            text=text.upper(),
            text_color=COLORS["label"],
            font=ctk.CTkFont(size=10),
        )
        label.pack(anchor="w", padx=4, pady=(0, 5))

    def add_nav_button(self, parent, panel_name, text, danger=False):
        button = ctk.CTkButton(
            parent,
            text=text,
            height=34,
            anchor="w",
            fg_color="transparent",
            hover_color=COLORS["panel_hover"] if not danger else COLORS["red_dark"],
            text_color=COLORS["text_soft"] if not danger else "#8d4a4a",
            font=ctk.CTkFont(size=13, weight="normal"),
            command=lambda: self.show_panel(panel_name),
        )
        button.pack(fill="x", pady=2)
        self.nav_buttons[panel_name] = {
            "button": button,
            "danger": danger,
            "text": text,
        }

    def reset_nav_buttons(self):
        for panel_name, data in self.nav_buttons.items():
            button = data["button"]
            danger = data["danger"]

            button.configure(
                fg_color="transparent",
                text_color=COLORS["text_soft"] if not danger else "#8d4a4a",
                font=ctk.CTkFont(size=13, weight="normal"),
            )

    def set_active_button(self, panel_name):
        if panel_name not in self.nav_buttons:
            return

        data = self.nav_buttons[panel_name]
        button = data["button"]

        button.configure(
            fg_color=COLORS["panel_active"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def show_panel(self, panel_name):
        self.current_panel = panel_name

        self.reset_nav_buttons()
        self.set_active_button(panel_name)
        self.clear_content()

        panel_titles = {
            "new_archive": "New archive",
            "add_folder": "Add folder",
            "update_folder": "Update folder",
            "search_archive": "Search archive",
            "show_root": "Show saved root",
            "clear_root": "Clear saved root",
            "customize_ui": "Customize UI",
        }

        title = panel_titles.get(panel_name, "Archive Builder")
        self.topbar_title.configure(text=title)

        if panel_name == "new_archive":
            self.panel_new_archive()
        elif panel_name == "add_folder":
            self.panel_add_folder()
        elif panel_name == "update_folder":
            self.panel_update_folder()
        elif panel_name == "search_archive":
            self.panel_search_archive()
        elif panel_name == "show_root":
            self.panel_show_root()
        elif panel_name == "clear_root":
            self.panel_clear_root()
            self.set_status(f"{title} selected.")
        elif panel_name == "customize_ui":
            self.panel_customize_ui()

    def panel_header(self, label):
        section = ctk.CTkLabel(
            self.content,
            text=label.upper(),
            text_color=COLORS["label"],
            font=ctk.CTkFont(size=10),
        )
        section.grid(row=0, column=0, sticky="w", pady=(0, 12))

    def create_action_card(self, row, title, subtitle, icon_text, color_key, command=None, featured=False):
        border_color = COLORS["border_active"] if featured else COLORS["border"]
        fg_color = COLORS["panel_active"] if featured else COLORS["panel"]

        card = ctk.CTkFrame(
            self.content,
            height=68,
            fg_color=fg_color,
            border_width=1,
            border_color=border_color,
            corner_radius=10,
        )
        card.grid(row=row, column=0, sticky="ew", pady=5)
        card.grid_columnconfigure(1, weight=1)
        card.grid_propagate(False)

        icon_bg = {
            "purple": COLORS["purple_dark"],
            "teal": COLORS["teal_dark"],
            "amber": COLORS["amber_dark"],
            "blue": COLORS["blue_dark"],
            "gray": COLORS["gray_icon"],
            "red": COLORS["red_dark"],
        }.get(color_key, COLORS["gray_icon"])

        icon_fg = {
            "purple": COLORS["purple_light"],
            "teal": COLORS["teal"],
            "amber": COLORS["amber"],
            "blue": COLORS["blue"],
            "gray": COLORS["text_soft"],
            "red": COLORS["red"],
        }.get(color_key, COLORS["text_soft"])

        icon = ctk.CTkLabel(
            card,
            text=icon_text,
            width=38,
            height=38,
            fg_color=icon_bg,
            text_color=icon_fg,
            corner_radius=8,
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        icon.grid(row=0, column=0, padx=(14, 12), pady=14)

        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.grid(row=0, column=1, sticky="w")

        title_label = ctk.CTkLabel(
            text_frame,
            text=title,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            text_frame,
            text=subtitle,
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(size=12),
        )
        subtitle_label.pack(anchor="w", pady=(1, 0))

        if featured:
            badge = ctk.CTkLabel(
                card,
                text="Active",
                fg_color=COLORS["purple"],
                text_color=COLORS["text"],
                corner_radius=20,
                width=54,
                height=22,
                font=ctk.CTkFont(size=11, weight="bold"),
            )
            badge.grid(row=0, column=2, padx=(8, 14))

        if command:
            card.bind("<Button-1>", lambda event: command())
            icon.bind("<Button-1>", lambda event: command())
            text_frame.bind("<Button-1>", lambda event: command())
            title_label.bind("<Button-1>", lambda event: command())
            subtitle_label.bind("<Button-1>", lambda event: command())

    def panel_new_archive(self):
        self.panel_header("Build archive")

        form = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=10,
        )
        form.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        form.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            form,
            text="Create a new archive",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(18, 4))

        subtitle = ctk.CTkLabel(
            form,
            text="Choose where the archive should be created. The app will generate the homepage, Conversations folder, current year, current month, and optional top-level folders.",
            text_color=COLORS["text_soft"],
            font=ctk.CTkFont(size=13),
            wraplength=620,
            justify="left",
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 18))

        archive_label = ctk.CTkLabel(
            form,
            text="Archive folder",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        archive_label.grid(row=2, column=0, sticky="w", padx=18, pady=(0, 6))

        self.new_archive_path_var = ctk.StringVar()

        archive_entry = ctk.CTkEntry(
            form,
            textvariable=self.new_archive_path_var,
            height=38,
            fg_color=COLORS["window"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text="Example: E:\\Documents\\ChatGPT Archives",
            placeholder_text_color=COLORS["text_muted"],
        )
        archive_entry.grid(row=3, column=0, sticky="ew", padx=(18, 8), pady=(0, 14))

        browse_button = ctk.CTkButton(
            form,
            text="Browse",
            width=90,
            height=38,
            fg_color=COLORS["purple"],
            hover_color="#3d3489",
            text_color="#e8e4ff",
            command=self.browse_new_archive_folder,
        )
        browse_button.grid(row=3, column=1, sticky="e", padx=(0, 18), pady=(0, 14))

        extra_label = ctk.CTkLabel(
            form,
            text="Extra top-level folders",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        extra_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 6))

        self.extra_folders_var = ctk.StringVar(value="Projects, Stories")

        extra_entry = ctk.CTkEntry(
            form,
            textvariable=self.extra_folders_var,
            height=38,
            fg_color=COLORS["window"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text="Projects, Stories, Dreams",
            placeholder_text_color=COLORS["text_muted"],
        )
        extra_entry.grid(row=5, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 18))

        years_label = ctk.CTkLabel(
            form,
            text="Years to create",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        years_label.grid(row=6, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 6))

        self.years_to_create_var = ctk.StringVar(value=str(datetime.now().year))

        years_entry = ctk.CTkEntry(
            form,
            textvariable=self.years_to_create_var,
            height=38,
            fg_color=COLORS["window"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text="Example: 2024, 2025, 2026",
            placeholder_text_color=COLORS["text_muted"],
        )
        years_entry.grid(row=7, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 12))

        self.create_all_months_var = ctk.BooleanVar(value=False)

        all_months_checkbox = ctk.CTkCheckBox(
            form,
            text="Create all months for selected years",
            variable=self.create_all_months_var,
            text_color=COLORS["text_soft"],
            fg_color=COLORS["purple"],
            hover_color="#3d3489",
            border_color=COLORS["border_active"],
        )
        all_months_checkbox.grid(row=8, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 18))

        build_button = ctk.CTkButton(
            form,
            text="+  Build archive",
            height=42,
            fg_color=COLORS["purple"],
            hover_color="#3d3489",
            text_color="#e8e4ff",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.build_new_archive_from_ui,
        )
        build_button.grid(row=9, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 18))

        self.create_action_card(
            row=2,
            title="Search archive",
            subtitle="Find conversations by keyword",
            icon_text="⌕",
            color_key="teal",
            command=lambda: self.show_panel("search_archive"),
        )

        self.create_action_card(
            row=3,
            title="Add folder",
            subtitle="Add a menu or conversation folder",
            icon_text="📁",
            color_key="amber",
            command=lambda: self.show_panel("add_folder"),
        )

        self.create_action_card(
            row=4,
            title="Update folder",
            subtitle="Patch files and update folder index",
            icon_text="↻",
            color_key="blue",
            command=lambda: self.show_panel("update_folder"),
        )

    def browse_new_archive_folder(self):
        folder = filedialog.askdirectory(
            title="Choose where to create the archive"
        )

        if folder:
            self.new_archive_path_var.set(folder)
            self.set_status("archive folder selected.")

    def build_new_archive_from_ui(self):
        raw_path = self.new_archive_path_var.get().strip().strip('"')

        if not raw_path:
            messagebox.showerror(
                "Missing archive folder",
                "Please choose or enter an archive folder first."
            )
            self.set_status("archive creation cancelled: no folder selected.")
            return

        archive_root = Path(raw_path)
        extra_folders = normalize_folder_names(self.extra_folders_var.get())

        try:
            years_to_create = parse_years(self.years_to_create_var.get())
            create_all_months = self.create_all_months_var.get()

            archive_path = build_archive(
                archive_root=archive_root,
                extra_folders=extra_folders,
                years_to_create=years_to_create,
                create_all_months=create_all_months,
            )

            set_archive_root(archive_path)
            self.saved_archive_root = archive_path

        except Exception as error:
            messagebox.showerror(
                "Archive creation failed",
                str(error)
            )
            self.set_status("archive creation failed.")
            return

        messagebox.showinfo(
            "Archive created",
            f"Archive created successfully:\n\n{archive_path}"
        )

        self.set_status("archive created successfully.")

    def panel_customize_ui(self):
        self.panel_header("Customize conversation UI")

        settings = get_conversation_ui_settings()
        self.ui_setting_vars = {}

        scroll = ctk.CTkScrollableFrame(
            self.content,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=10,
            
        )
        scroll.grid(row=1, column=0, sticky="nsew", pady=(0, 14))
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            scroll,
            text="Conversation UI settings",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(18, 4))

        subtitle = ctk.CTkLabel(
            scroll,
            text="These settings generate a local conversation UI patch. They will apply to future folder updates. To apply them to old conversations, run Update folder again.",
            text_color=COLORS["text_soft"],
            font=ctk.CTkFont(size=13),
            wraplength=620,
            justify="left",
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 18))

        fields = [
            ("background_color", "Background color", "Example: #212121"),
            ("text_color", "Text color", "Example: #ececec"),
            ("user_bubble_color", "User bubble color", "Example: #ab68ff"),
            ("user_bubble_opacity", "User bubble opacity", "0 to 1"),
            ("user_bubble_border_opacity", "Bubble border opacity", "0 to 1"),
            ("font_size", "Font size", "10 to 32"),
            ("line_height", "Line height", "16 to 60"),
            ("conversation_max_width", "Conversation max width", "600 to 2000"),
            ("user_message_max_width", "User message max width", "300 to 1600"),
            ("assistant_message_max_width", "Assistant message max width", "300 to 1600"),
            ("image_max_width", "Image max width", "100 to 1200"),
        ]

        row = 2

        for key, label_text, placeholder in fields:
            label = ctk.CTkLabel(
                scroll,
                text=label_text,
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=13, weight="bold"),
            )
            label.grid(row=row, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 6))

            var = ctk.StringVar(value=str(settings.get(key, "")))
            self.ui_setting_vars[key] = var

            entry = ctk.CTkEntry(
                scroll,
                textvariable=var,
                height=36,
                fg_color=COLORS["window"],
                border_color=COLORS["border"],
                text_color=COLORS["text"],
                placeholder_text=placeholder,
                placeholder_text_color=COLORS["text_muted"],
            )

            if key in ["background_color", "text_color", "user_bubble_color"]:
                entry.grid(row=row + 1, column=0, sticky="ew", padx=(18, 8), pady=(0, 12))

                pick_button = ctk.CTkButton(
                    scroll,
                    text="Pick",
                    height=36,
                    width=90,
                    fg_color=COLORS["panel_active"],
                    hover_color=COLORS["panel_hover"],
                    text_color=COLORS["text"],
                    command=lambda setting_key=key: self.pick_ui_color(setting_key),
                )
                pick_button.grid(row=row + 1, column=1, sticky="e", padx=(0, 18), pady=(0, 12))

            else:
                entry.grid(row=row + 1, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 12))

            row += 2

        avatar_title = ctk.CTkLabel(
            scroll,
            text="Avatars",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        avatar_title.grid(row=row, column=0, columnspan=2, sticky="w", padx=18, pady=(12, 8))
        row += 1

        self.user_avatar_status_var = ctk.StringVar(
            value="User avatar: enabled"
            if settings.get("user_avatar_enabled") == "true" and settings.get("user_avatar_data_uri")
            else "User avatar: default"
        )

        user_avatar_status = ctk.CTkLabel(
            scroll,
            textvariable=self.user_avatar_status_var,
            text_color=COLORS["text_soft"],
            font=ctk.CTkFont(size=13),
        )
        user_avatar_status.grid(row=row, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 6))
        row += 1

        user_avatar_button = ctk.CTkButton(
            scroll,
            text="Choose user avatar",
            height=38,
            fg_color=COLORS["panel_active"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["text"],
            command=lambda: self.choose_avatar_from_ui("user"),
        )
        user_avatar_button.grid(row=row, column=0, sticky="ew", padx=(18, 8), pady=(0, 10))

        clear_user_avatar_button = ctk.CTkButton(
            scroll,
            text="Clear user avatar",
            height=38,
            fg_color=COLORS["panel_active"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["text"],
            command=lambda: self.clear_avatar_from_ui("user"),
        )
        clear_user_avatar_button.grid(row=row, column=1, sticky="ew", padx=(8, 18), pady=(0, 10))
        row += 1

        self.assistant_avatar_status_var = ctk.StringVar(
            value="Assistant avatar: enabled"
            if settings.get("assistant_avatar_enabled") == "true" and settings.get("assistant_avatar_data_uri")
            else "Assistant avatar: default"
        )

        assistant_avatar_status = ctk.CTkLabel(
            scroll,
            textvariable=self.assistant_avatar_status_var,
            text_color=COLORS["text_soft"],
            font=ctk.CTkFont(size=13),
        )
        assistant_avatar_status.grid(row=row, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 6))
        row += 1

        assistant_avatar_button = ctk.CTkButton(
            scroll,
            text="Choose assistant avatar",
            height=38,
            fg_color=COLORS["panel_active"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["text"],
            command=lambda: self.choose_avatar_from_ui("assistant"),
        )
        assistant_avatar_button.grid(row=row, column=0, sticky="ew", padx=(18, 8), pady=(0, 18))

        clear_assistant_avatar_button = ctk.CTkButton(
            scroll,
            text="Clear assistant avatar",
            height=38,
            fg_color=COLORS["panel_active"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["text"],
            command=lambda: self.clear_avatar_from_ui("assistant"),
        )
        clear_assistant_avatar_button.grid(row=row, column=1, sticky="ew", padx=(8, 18), pady=(0, 18))
        row += 1

        save_button = ctk.CTkButton(
            scroll,
            text="⚙  Save and generate UI patch",
            height=42,
            fg_color=COLORS["purple"],
            hover_color="#3d3489",
            text_color="#e8e4ff",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.save_conversation_ui_settings_from_ui,
        )
        save_button.grid(row=row, column=0, sticky="ew", padx=(18, 8), pady=(8, 18))

        reset_button = ctk.CTkButton(
            scroll,
            text="Reset to default",
            height=42,
            fg_color=COLORS["panel_active"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.reset_conversation_ui_settings_from_ui,
        )
        reset_button.grid(row=row, column=1, sticky="ew", padx=(8, 18), pady=(8, 18))

    def choose_avatar_from_ui(self, avatar_type):
        if not hasattr(self, "ui_setting_vars"):
            self.set_status("no UI settings loaded.")
            return

        file_path = filedialog.askopenfilename(
            title=f"Choose {avatar_type} avatar",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.gif"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("WEBP files", "*.webp"),
                ("GIF files", "*.gif"),
                ("All files", "*.*"),
            ],
        )

        if not file_path:
            self.set_status("avatar selection cancelled.")
            return

        try:
            data_uri = image_file_to_data_uri(Path(file_path))

        except Exception as error:
            messagebox.showerror(
                "Avatar failed",
                str(error)
            )
            self.set_status("avatar selection failed.")
            return

        enabled_key = f"{avatar_type}_avatar_enabled"
        data_key = f"{avatar_type}_avatar_data_uri"

        self.ui_setting_vars[enabled_key] = ctk.StringVar(value="true")
        self.ui_setting_vars[data_key] = ctk.StringVar(value=data_uri)

        if avatar_type == "user" and hasattr(self, "user_avatar_status_var"):
            self.user_avatar_status_var.set("User avatar: selected, not saved yet")

        if avatar_type == "assistant" and hasattr(self, "assistant_avatar_status_var"):
            self.assistant_avatar_status_var.set("Assistant avatar: selected, not saved yet")

        self.set_status(f"{avatar_type} avatar selected.")


    def clear_avatar_from_ui(self, avatar_type):
        if not hasattr(self, "ui_setting_vars"):
            self.set_status("no UI settings loaded.")
            return

        enabled_key = f"{avatar_type}_avatar_enabled"
        data_key = f"{avatar_type}_avatar_data_uri"

        self.ui_setting_vars[enabled_key] = ctk.StringVar(value="false")
        self.ui_setting_vars[data_key] = ctk.StringVar(value="")

        if avatar_type == "user" and hasattr(self, "user_avatar_status_var"):
            self.user_avatar_status_var.set("User avatar: cleared, not saved yet")

        if avatar_type == "assistant" and hasattr(self, "assistant_avatar_status_var"):
            self.assistant_avatar_status_var.set("Assistant avatar: cleared, not saved yet")

        self.set_status(f"{avatar_type} avatar cleared.")

    def pick_ui_color(self, setting_key):
        if not hasattr(self, "ui_setting_vars"):
            self.set_status("no UI settings loaded.")
            return

        current_color = self.ui_setting_vars[setting_key].get().strip()

        if not current_color.startswith("#"):
            current_color = "#ffffff"

        chosen_color = colorchooser.askcolor(
            color=current_color,
            title="Choose color"
        )

        hex_color = chosen_color[1]

        if not hex_color:
            self.set_status("color selection cancelled.")
            return

        self.ui_setting_vars[setting_key].set(hex_color)
        self.set_status(f"{setting_key} color selected.")

    def save_conversation_ui_settings_from_ui(self):
        if not hasattr(self, "ui_setting_vars"):
            self.set_status("no UI settings loaded.")
            return

        updates = {
            key: var.get().strip()
            for key, var in self.ui_setting_vars.items()
        }

        try:
            patch_path = save_and_generate_conversation_ui_patch(updates)

        except Exception as error:
            messagebox.showerror(
                "UI settings failed",
                str(error)
            )
            self.set_status("conversation UI settings failed.")
            return

        messagebox.showinfo(
            "Conversation UI saved",
            f"Conversation UI settings were saved.\n\n"
            f"Generated patch:\n{patch_path}\n\n"
            "Run Update folder to apply this UI to conversations."
        )

        if hasattr(self, "user_avatar_status_var"):
            user_avatar_active = (
                updates.get("user_avatar_enabled") == "true"
                and updates.get("user_avatar_data_uri")
            )

            self.user_avatar_status_var.set(
                "User avatar: enabled" if user_avatar_active else "User avatar: default"
            )

        if hasattr(self, "assistant_avatar_status_var"):
            assistant_avatar_active = (
                updates.get("assistant_avatar_enabled") == "true"
                and updates.get("assistant_avatar_data_uri")
            )

            self.assistant_avatar_status_var.set(
                "Assistant avatar: enabled" if assistant_avatar_active else "Assistant avatar: default"
            )

        self.set_status("conversation UI patch generated.")


    def reset_conversation_ui_settings_from_ui(self):
        confirm = messagebox.askyesno(
            "Reset conversation UI",
            "Reset conversation UI settings to the default values?"
        )

        if not confirm:
            self.set_status("conversation UI reset cancelled.")
            return

        try:
            patch_path = reset_conversation_ui_patch()

        except Exception as error:
            messagebox.showerror(
                "Reset failed",
                str(error)
            )
            self.set_status("conversation UI reset failed.")
            return

        messagebox.showinfo(
            "Conversation UI reset",
            f"Conversation UI settings were reset.\n\n"
            f"Generated patch:\n{patch_path}\n\n"
            "Run Update folder to apply the default UI to conversations."
        )

        self.set_status("conversation UI reset to default.")
        self.show_panel("customize_ui")

    def panel_simple_message(self, title, message):
        self.panel_header(title)

        box = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=10,
        )
        box.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        box.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            box,
            text=title,
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        title_label.grid(row=0, column=0, sticky="w", padx=18, pady=(18, 4))

        message_label = ctk.CTkLabel(
            box,
            text=message,
            text_color=COLORS["text_soft"],
            font=ctk.CTkFont(size=13),
            wraplength=560,
            justify="left",
        )
        message_label.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 18))

    def set_status(self, message):
        root_text = str(self.saved_archive_root) if self.saved_archive_root else "not defined"
        self.status_text.configure(text=f"root: {root_text} — {message}")


def main():
    app = ArchiveBuilderUI()
    app.mainloop()


if __name__ == "__main__":
    main()