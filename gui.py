### gui.py
import tkinter as tk
from tkinter import ttk
import threading
from gcp import analyze_user_chunks

def run_gui():
    def run_analysis():
        user_id = user_entry.get().strip()
        if not user_id:
            output_box.insert(tk.END, "Please enter a user ID.\n")
            return

        output_box.insert(tk.END, f"\nRunning analysis for user: {user_id}...\n")

        def run():
            try:
                results = analyze_user_chunks(user_id)
                output_box.insert(tk.END, f"Found {len(results)} memory folders:\n\n")
                for res in results:
                    output_box.insert(tk.END, f"Memory: {res['memory_id']}\n")
                    output_box.insert(tk.END, f"  Created at: {res['created_at']}\n")
                    output_box.insert(tk.END, f"  Chunks: {res['chunk_count']}\n")
                    output_box.insert(tk.END, f"  Total Size: {res['total_size_kb']:.2f} KB\n")
                    output_box.insert(tk.END, f"  Avg Chunk Size: {res['avg_chunk_size_kb']:.2f} KB\n")
                    output_box.insert(tk.END, f"  Estimated Duration: {res['estimated_duration_sec']:.2f} sec\n\n")
            except Exception as e:
                output_box.insert(tk.END, f"Error: {e}\n")

        threading.Thread(target=run).start()

    root = tk.Tk()
    root.title("Neo1 Chunk Analyzer")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    tk.Label(frame, text="User ID:").grid(row=0, column=0, sticky=tk.W)
    user_entry = tk.Entry(frame, width=40)
    user_entry.grid(row=0, column=1)

    run_btn = tk.Button(frame, text="Analyze", command=run_analysis)
    run_btn.grid(row=0, column=2, padx=5)

    output_box = tk.Text(root, height=30, width=100)
    output_box.pack(padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    run_gui()

