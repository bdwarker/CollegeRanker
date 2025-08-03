import sys
import subprocess

required_modules = ["tkinter", "pandas", "openpyxl", "json"]
saved_ranks = {}  # (college, branch) => rank string
missing = []
for mod in required_modules:
    try:
        if mod == "tkinter":
            import tkinter as tk
            from tkinter import filedialog, ttk, messagebox
        elif mod == "pandas":
            import pandas as pd
        elif mod == "json":
            import json
    except ImportError:
        missing.append(mod)

if missing:
    print(f"\nMissing required modules: {', '.join(missing)}")
    choice = input("Do you want to install them now? (y/n): ").strip().lower()
    if choice == 'y':
        for mod in missing:
            print(f"Installing {mod}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", mod])
        print("\nAll required modules installed. Please rerun the program.\n")
        sys.exit()
    else:
        print("Cannot run without required modules. Exiting.")
        sys.exit()

branch_keywords = {
    "CSE": ["computer", "computing", "software", "data"],
    "ECE": ["electronics", "communication"],
    "ME": ["mechanical", "mech"],
    "EE": ["electrical"],
    "CE": ["civil", "construction"],
    "CHE": ["chemical", "chemistry"],
    "IT": ["information", "it"],
    "MATH": ["mathematics", "maths"]
}

def get_branch_code(branch_name):
    name_lower = branch_name.lower()
    for code, keywords in branch_keywords.items():
        if any(keyword in name_lower for keyword in keywords):
            return code
    return "OTHERS"

rank_entries = {}
current_data = {}
selected = None
scrollable_frame = None

def export_to_excel():
    data = []
    ranks_seen = {}
    conflicts = []

    for (college, branch), entry in rank_entries.items():
        rank = entry.get().strip()
        if rank.isdigit():
            rank = int(rank)
            if rank in ranks_seen:
                conflicts.append((rank, ranks_seen[rank], (college, branch)))
            else:
                ranks_seen[rank] = (college, branch)
            branch_code = get_branch_code(branch)
            data.append({
                "RANK GIVEN BY USER": rank,
                "COLLEGE NAME": college,
                "BRANCH NAME": branch,
                "BRANCH CODE": branch_code
            })

    if conflicts:
        conflict_msg = "\n".join(
            f"Rank {rank} is assigned to:\n  - {c1[0]}: {c1[1]}\n  - {c2[0]}: {c2[1]}"
            for rank, c1, c2 in conflicts
        )
        messagebox.showwarning("Duplicate Ranks Detected", f"Conflicting ranks found:\n\n{conflict_msg}\n\nPlease assign unique ranks.")
        return

    df = pd.DataFrame(data)
    df = df.sort_values(by="RANK GIVEN BY USER")
    df.to_excel("college_rankings.xlsx", index=False)
    messagebox.showinfo("Exported", "Rankings exported to college_rankings.xlsx")
def load_rankings_from_excel():
    try:
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return

        df = pd.read_excel(file_path)
        for _, row in df.iterrows():
            college = row["COLLEGE NAME"]
            branch = row["BRANCH NAME"]
            rank = str(row["RANK GIVEN BY USER"])
            key = (college, branch)
            if key in rank_entries:
                rank_entries[key].delete(0, tk.END)
                rank_entries[key].insert(0, rank)
        messagebox.showinfo("Success", "Rankings loaded successfully into the GUI.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load rankings:\n{str(e)}")

def load_json_file():
    global current_data
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if not file_path:
        return
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError("JSON is not in correct format")
        current_data = data
        refresh_gui(selected.get())
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load JSON file:\n{str(e)}")

def refresh_gui(branch_code):
    # Save existing GUI entry values into saved_ranks
    for (college, branch), entry in rank_entries.items():
        saved_ranks[(college, branch)] = entry.get()

    # Clear GUI widgets
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    rank_entries.clear()

    row_idx = 0
    for college, branches in current_data.items():
        filtered = [b for b in branches if branch_code == "ALL" or get_branch_code(b) == branch_code]
        if not filtered:
            continue

        college_label = ttk.Label(scrollable_frame, text=college, font=("Helvetica", 14, "bold"))
        college_label.grid(row=row_idx, column=0, sticky="w", padx=10, pady=(10, 0))
        row_idx += 1

        for branch in filtered:
            ttk.Label(scrollable_frame, text=branch, width=70).grid(row=row_idx, column=0, sticky="w", padx=30, pady=2)
            entry = ttk.Entry(scrollable_frame, width=10)
            entry.grid(row=row_idx, column=1, sticky="w", padx=10)

            key = (college, branch)
            if key in saved_ranks:
                entry.insert(0, saved_ranks[key])  # Restore previous value

            rank_entries[key] = entry
            row_idx += 1

def main_gui():
    global selected, scrollable_frame

    root = tk.Tk()
    root.title("College Ranking System")
    root.geometry("1200x750")
    root.resizable(True, True)

    # --- Fixed top bar ---
    top_bar = ttk.Frame(root)
    top_bar.pack(fill="x", padx=10, pady=5)

    ttk.Label(top_bar, text="Sort by Branch:").pack(side="left")
    selected = tk.StringVar(value="ALL")
    ttk.OptionMenu(top_bar, selected, "ALL", *branch_options, command=refresh_gui).pack(side="left", padx=10)

    ttk.Button(top_bar, text="Load JSON File", command=load_json_file).pack(side="left", padx=10)
    ttk.Button(top_bar, text="Load Rankings from Excel", command=load_rankings_from_excel).pack(side="right", padx=10)
    ttk.Button(top_bar, text="Export to Excel", command=export_to_excel).pack(side="right", padx=10)

    # --- Canvas + Scrollable content ---
    outer_frame = ttk.Frame(root)
    outer_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(outer_frame)
    scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    content_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=content_frame, anchor="nw")

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    content_frame.bind("<Configure>", on_frame_configure)

    scrollable_frame = content_frame
    refresh_gui("ALL")

    root.mainloop()

branch_options = ["ALL"] + list(branch_keywords.keys())

if __name__ == "__main__":
    main_gui()
