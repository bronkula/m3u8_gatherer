import subprocess
import threading
import re
import tkinter as tk
from tkinter import filedialog

# Queue to hold m3u8 files
queue = []
queue_rows = []
width=800
height=600
queue_position = 0

def save_m3u8():
    enqueue_m3u8()
    process_queue()

    # try:
    #     subprocess.run(['ffmpeg', '-i', url, '-c', 'copy', output_filename])
    #     result_label.config(text=f"m3u8 file saved as {output_filename}")
    # except Exception as e:
    #     result_label.config(text=f"An error occurred: {e}")

def browse_output(widget):
    output_filename = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("mp4 files", "*.mp4"), ("all files", "*.*")])
    if output_filename:
        widget.delete(0, tk.END)
        widget.insert(0, output_filename)

def enqueue_m3u8(url, output_filename):
    queue.append([url, output_filename, 0])
    update_queue_table()
    # clear_initial_form()

def update_list_url_from_input(idx):
    queue[idx] = (queue_rows[idx][0].get(), queue[idx][1])

def update_list_output_from_input(idx):
    queue[idx] = (queue[idx][0], queue_rows[idx][1].get())

def update_list_size_with_value(idx, value):
    queue_rows[idx][2].delete(0, tk.END)
    queue_rows[idx][2].insert(0, value)

# def clear_initial_form():
#     url_entry.delete(0, tk.END)
#     output_entry.delete(0, tk.END)

def update_queue_table():
    for row in queue_rows:
        for entry in row:
            entry.destroy()

    queue_rows.clear()

    for idx, (url, output, size) in enumerate(queue):
        url_entry = tk.Entry(queue_frame, width=60)
        url_entry.insert(0, url)
        url_entry.bind('<FocusOut>', lambda event, idx=idx: update_list_url_from_input(idx))
        url_entry.grid(row=idx, column=0)
        
        output_entry = tk.Entry(queue_frame, width=30)
        output_entry.insert(0, output)
        output_entry.bind('<FocusOut>', lambda event, idx=idx: update_list_output_from_input(idx))
        output_entry.grid(row=idx, column=1)
        
        position_entry = tk.Entry(queue_frame, width=10)
        position_entry.insert(0, size)
        position_entry.grid(row=idx, column=2)
        
        queue_rows.append((url_entry, output_entry, position_entry))

def clear_queue():
    queue.clear()
    update_queue_table()

def paste_from_clipboard_on_focus(event):
    event.widget.delete(0, tk.END)
    event.widget.insert(0, window.clipboard_get())

def paste_from_clipboard_to_widget(widget):
    widget.delete(0, tk.END)
    widget.insert(0, window.clipboard_get())

def process_queue():
    global queue_position
    if queue_position < len(queue):
        url, output_filename, size = queue[queue_position]
        if size > 0:
            result_label.config(text=f"Skipping {output_filename} because it already exists.")
            queue_position += 1
            process_queue()
            return
        try:
            process = subprocess.Popen(['ffmpeg', '-nostdin', '-i', url, '-c', 'copy', output_filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

            threading.Thread(target=update_progress, args=(process, output_filename), daemon=True).start()
        except Exception as e:
            result_label.config(text=f"An error occurred: {e}")
            process_queue()
    else:
        result_label.config(text="Queue is empty.")
        queue_position = 0

def create_modal_window(width=400, height=300):

    x = window.winfo_x()
    y = window.winfo_y()
    w = window.winfo_width()
    h = window.winfo_height()

    modal_window = tk.Toplevel(window)
    modal_window.geometry(f'+{x + w//2 - width//2}+{y + h//2 - height//2}')
    modal_window.title("Modal Window")
    modal_window.transient(window)
    modal_window.grab_set()
    modal_window.focus_set()

    return modal_window

def make_add_new_modal():
    modal_window = create_modal_window()

    modal_frame = tk.Frame(modal_window, width=width//2, height=height//2)
    modal_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=10, pady=10)

    url_label = tk.Label(modal_frame, text="URL:")
    url_label.grid(row=0, column=0, sticky=tk.W)
    url_entry = tk.Entry(modal_frame, width=30)
    url_entry.insert(0, window.clipboard_get())
    url_entry.grid(row=0, column=1, sticky=tk.W)

    output_label = tk.Label(modal_frame, text="Output Filename:")
    output_label.grid(row=1, column=0, sticky=tk.W)
    output_entry = tk.Entry(modal_frame, width=30)
    output_entry.grid(row=1, column=1, sticky=tk.W)
    browse_button = tk.Button(modal_frame, text="Browse", command=lambda: browse_output(output_entry))
    browse_button.grid(row=1, column=2, sticky=tk.W)

    def add_to_queue():
        enqueue_m3u8(url_entry.get(), output_entry.get())
        modal_window.destroy()

    cancel_button = tk.Button(modal_frame, text="Cancel", command=modal_window.destroy)
    cancel_button.grid(row=2, column=0, sticky=tk.W)

    add_button = tk.Button(modal_frame, text="Add", command=add_to_queue)
    add_button.grid(row=2, column=1, sticky=tk.E)

def update_progress(process, output_filename):
    global queue_position
    while process.poll() is None:
        # Update output text area
        output_line = process.stdout.readline()
        if output_line:
            p = re.compile('dts = (\d+)')
            m = p.search(output_line)
            if m:
                size = ""
                bps = int(m.group(1))
                if bps > 0:
                    mbs = bps / (1024*1024)
                    gbs = mbs / 1024
                    if gbs > 1:
                        queue[queue_position][2] = f'{gbs:.2f} GB'
                    elif mbs > 1:
                        queue[queue_position][2] = f'{mbs:.2f} MB'
                    else:
                        queue[queue_position][2] = f'{bps} B'
                else:
                    queue[queue_position][2] = f'0'

                update_list_size_with_value(queue_position, queue[queue_position][2])

            output_text.delete('1.0', tk.END)
            output_text.insert(tk.END, output_line)
            output_text.see(tk.END)
            queue_frame.update_idletasks()
    
            
    result_label.config(text=f"m3u8 file saved as {output_filename}")
    update_queue_table()
    queue_position += 1
    process_queue()

# Create the main window
window = tk.Tk()
window.title("m3u8 Downloader")

# Left side - Inputs

right_top_frame = tk.Frame(window, width=500, height=400)
right_top_frame.grid(row=0, column=0, padx=10, pady=10)
right_middle_frame = tk.Frame(window, width=500, height=100)
right_middle_frame.grid(row=1, column=0, padx=10, pady=10)
right_bottom_frame = tk.Frame(window, width=500, height=100)
right_bottom_frame.grid(row=2, column=0)

# Right side - Queue Table

queue_label = tk.Label(right_top_frame, text="Queue:")
queue_label.grid(row=0, column=0, sticky=tk.W)

add_new_button = tk.Button(right_top_frame, text="+ Add", command=make_add_new_modal)
add_new_button.grid(row=0, column=1, sticky=tk.E)

queue_frame = tk.Frame(right_top_frame)
queue_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=10)

update_queue_table()

clear_queue_button = tk.Button(right_middle_frame, text="Clear Queue", command=clear_queue)
clear_queue_button.grid(row=0, column=0, sticky=tk.E)
process_queue_button = tk.Button(right_middle_frame, text="Process Queue", command=process_queue)
process_queue_button.grid(row=0, column=1, sticky=tk.E)

# Result label
result_label = tk.Label(right_bottom_frame, text="")
result_label.grid(row=0, column=0, columnspan=2)

output_text = tk.Text(right_bottom_frame, wrap=tk.WORD, height=10)
output_text.grid(row=len(queue_rows) + 1, columnspan=2, sticky='ew')

# Start the GUI event loop
window.mainloop()