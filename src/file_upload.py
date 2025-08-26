import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import pandas as pd
import time  # Simulate processing delay
# from main import process_domains

def update_progress(i, total):
    progress_bar['maximum'] = total
    progress_bar['value'] = i
    progress_label.config(text=f"Processed: {i} / {total}")
    root.update_idletasks()


def start_processing(domains):
    # process_domains(domains, progress_callback=update_progress)
    messagebox.showinfo("Done", "Processing complete!")


def upload_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("CSV files", "*.csv")],
        title="Select a CSV file"
    )
    
    if file_path:
        try:
            df = pd.read_csv(file_path)
            if "Domain" not in df.columns:
                messagebox.showerror("Invalid Format", "The CSV must contain a column named 'Domain'.")
                return
            if not all(df["Domain"].astype(str).str.startswith("https://")):
                messagebox.showerror("Invalid Data", "All domains must start with 'https://'.")
                return
        
            domains = df["Domain"].tolist()
            messagebox.showinfo("Thanks", "Will Process this soon!")
            # process_domains(domains)        
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file:\n{e}")

# Main window
root = tk.Tk()
root.title("Cookie Banner Scraper")
root.geometry("500x650")

# Heading
title_label = tk.Label(root, text="Cookie Banner Scraper", font=("Helvetica", 16, "bold"))
title_label.pack(pady=10)

# Guidelines
guidelines_text = (
    "Guidelines:\n"
    "1. Please upload a CSV file with one column named: \"Domain\"\n"
    "2. Each domain must begin with \"https://\"\n"
    "3. All domains that failed to be processed will be saved in the screenshots folder with the domain name.\n"
    "4. The resulting data will be saved in a new CSV file named 'results.csv'.\n"
)
guidelines_label = tk.Label(root, text=guidelines_text, justify="left", anchor="w", font=("Helvetica", 11))
guidelines_label.pack(padx=10, anchor="w")

# Image
tk.Label(root, text="Example:", font=("Helvetica", 12, "bold")).pack(pady=10)
image_path = "../example.png"
pil_img = Image.open(image_path)
pil_img = pil_img.resize((400, 250), Image.Resampling.LANCZOS)
img = ImageTk.PhotoImage(pil_img)

image_label = tk.Label(root, image=img)
image_label.image = img 
image_label.pack(pady=10)

# Upload button
upload_button = tk.Button(root, text="Upload CSV File", command=upload_file, font=("Helvetica", 12))
upload_button.pack(pady=20)

# Progress bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=5)

progress_label = tk.Label(root, text="Processed: 0 / 0")
progress_label.pack()

# Run GUI
root.mainloop()