import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from gcp import analyze_user_chunks

def run_gui():
    def run_analysis():
        user_id = user_entry.get().strip()
        if not user_id:
            output_box.insert(tk.END, "Please enter a user ID.\n")
            output_box.see(tk.END)  # Auto-scroll to the latest entry
            return

        output_box.insert(tk.END, f"\nRunning analysis for user: {user_id}...\n")
        output_box.see(tk.END)  # Auto-scroll to the latest entry

        def run():
            try:
                results = analyze_user_chunks(user_id)
                if not results:
                    output_box.insert(tk.END, "No data found for the given user ID.\n")
                    output_box.see(tk.END)  # Auto-scroll to the latest entry
                    return

                # Clear existing table data
                for row in tree.get_children():
                    tree.delete(row)

                for res in results:
                    tree.insert("", "end", values=(
                        res['memory_id'],
                        res['created_at'],
                        res['chunk_count'],
                        f"{res['total_size_kb']:.2f}",
                        f"{res['avg_chunk_size_kb']:.2f}",
                        f"{res['estimated_duration_sec']:.2f}",
                        f"{res['smallest_chunk_kb']:.2f}",
                        f"{res['largest_chunk_kb']:.2f}"
                    ))

                output_box.insert(tk.END, "Analysis complete.\n")
                output_box.see(tk.END)  # Auto-scroll to the latest entry

            except Exception as e:
                output_box.insert(tk.END, f"Error: {e}\n")
                output_box.see(tk.END)  # Auto-scroll to the latest entry

        threading.Thread(target=run).start()

    def copy_treeview_cell(event):
        """Copy the content of the double-clicked cell to the clipboard and display it in the output_box."""
        # Identify the region and column where the double-click occurred
        region = tree.identify("region", event.x, event.y)
        if region == "cell":
            column = tree.identify_column(event.x)
            column_index = int(column[1:]) - 1  # Convert from '#1' to 0-based index
            selected_item = tree.selection()[0]
            cell_value = tree.item(selected_item, "values")[column_index]

            # Format the text
            formatted_text = f"{cell_value}\n"
            with open("clipboard", "w") as f:
                f.write(cell_value)

            # Copy to clipboard
            root.clipboard_clear()
            root.clipboard_append(formatted_text)
            root.update()  # Ensure the clipboard is updated immediately

            # Display in the output_box
            output_box.insert(tk.END, formatted_text + "\n")
            output_box.see(tk.END)  # Auto-scroll to the latest entry

    def enable_copy(event):
        """Enable copying of selected text in the output_box."""
        output_box.event_generate("<<Copy>>")
        return 'break'

    root = tk.Tk()
    root.title("Neo1 Chunk Analyzer")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    tk.Label(frame, text="User ID:").grid(row=0, column=0, sticky=tk.W)
    user_entry = tk.Entry(frame, width=40)
    user_entry.grid(row=0, column=1)

    run_btn = tk.Button(frame, text="Analyze", command=run_analysis)
    run_btn.grid(row=0, column=2, padx=5)

    columns = ("Memory ID", "Created At", "Chunk Count", "Total Size (KB)", "Avg Chunk Size (KB)", "Estimated Duration (s)", "Smallest Chunk (KB)", "Largest Chunk (KB)")
    tree = ttk.Treeview(root, columns=columns, show="headings", selectmode="browse")
    tree.pack(padx=10, pady=10, fill="both", expand=True)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    # Bind double-click event to the Treeview
    tree.bind("<Double-1>", copy_treeview_cell)

    # ScrolledText widget for output
    output_box = scrolledtext.ScrolledText(root, height=10, width=100, wrap=tk.WORD)
    output_box.pack(padx=10, pady=10, fill="both", expand=True)

    # Bind Ctrl+C to enable copying in the output_box
    output_box.bind("<Control-c>", enable_copy)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
