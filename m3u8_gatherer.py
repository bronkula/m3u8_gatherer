import subprocess
import threading
import re
import tkinter as tk
from tkinter import filedialog

# Queue to hold m3u8 files
queue = []
table_rows = []
table_header = [
    "URL",
    "Output Filename",
    "Size",
    "%",
    ""
]
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
    full_output, duration, dimensions = query_m3u8(url)

    # m3u8 url, output filename, size, duration, width, height, completion percentage
    queue.append([url, output_filename, 0, duration, dimensions[0], dimensions[1], 0])
    update_queue_table()
    # clear_initial_form()

def update_list_entry_with_value(widget, value):
    widget.delete(0, tk.END)
    widget.insert(0, value)
def update_list_value_from_entry(event):
    q_index = event.widget.grid_info()['row'] - 1
    index = event.widget.grid_info()['column']
    value = event.widget.get()
    queue[q_index][index] = value
    
def create_table_header():
    headers = []
    for index, header in enumerate(table_header):
        h = tk.Label(queue_frame, text=header, padx=10)
        h.grid(row=0, column=index, sticky="w")
        headers.append(h)

    table_rows.append(headers)

def destroy_table():
    for row in table_rows:
        for entry in row:
            entry.destroy()
    table_rows.clear()

def create_table_row(index, append=True):
    url, output, size, duration, width, height, percentage = queue[index]

    url_entry = tk.Entry(queue_frame, width=60)
    url_entry.insert(0, url)
    url_entry.bind('<FocusOut>', update_list_value_from_entry)
    url_entry.grid(row=index+1, column=0, sticky="nsew")
    
    output_entry = tk.Entry(queue_frame, width=60)
    output_entry.insert(0, output)
    output_entry.bind('<FocusOut>', update_list_value_from_entry)
    output_entry.grid(row=index+1, column=1, sticky="nsew")
    
    position_entry = tk.Entry(queue_frame, width=8)
    position_entry.insert(0, size)
    position_entry.grid(row=index+1, column=2, sticky="nsew")
    
    percentage_entry = tk.Entry(queue_frame, width=7)
    percentage_entry.insert(0, f'{percentage:.1f}%')
    percentage_entry.grid(row=index+1, column=3, sticky="nsew")

    # button that will query m3u8 file
    # query_button = tk.Button(queue_frame, text="?", command=lambda e: query_m3u8(url), width=5)
    # query_button.grid(row=index+1, column=4, sticky="nsew")

    if append == True:
        table_rows.append([url_entry, output_entry, position_entry, percentage_entry])
    return url_entry, output_entry, position_entry, percentage_entry

def update_table_row(index):
    # if table_rows index does not exist, create it
    table_index = index + 1
    if table_index >= len(table_rows):
        create_table_row(index)

    else:
        url, output, size, duration, width, height, percentage = queue[index]
        url_entry, output_entry, position_entry, percentage_entry = table_rows[index+1]
        update_list_entry_with_value(url_entry, url)
        update_list_entry_with_value(output_entry, output)
        update_list_entry_with_value(position_entry, size)
        update_list_entry_with_value(percentage_entry, f'{percentage:.1f}%')


def create_queue_table():
    destroy_table()
    if len(queue) > 0:
        create_table_header()
    
    for index in range(len(queue)):
        create_table_row(index)

def update_queue_table(destroy=False):
    if destroy:
        destroy_table()
    if len(table_rows) == 0:
        create_queue_table()
    else:
        for index in range(len(queue)):
            update_table_row(index)
    

def clear_queue():
    queue.clear()
    destroy_table()

def paste_from_clipboard_on_focus(event):
    event.widget.delete(0, tk.END)
    event.widget.insert(0, window.clipboard_get())

def paste_from_clipboard_to_widget(widget):
    widget.delete(0, tk.END)
    widget.insert(0, window.clipboard_get())


# function that will call ffmpeg and output result to text area
def query_m3u8(url):
    try:
        process = subprocess.Popen(['ffmpeg', '-y', '-i', url, '-map', '?'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        # threading.Thread(target=get_m3u8_data, args=[process], daemon=True).start()
        full_output, duration, dimensions = get_m3u8_data(process)
        return full_output, duration, dimensions
    except Exception as e:
        result_label.config(text=f"An error occurred: {e}")

def get_m3u8_data(process):
    full_output = ""
    duration = 0
    dimensions = (0, 0)

    while process.poll() is None:
        # Update output text area
        output_line = process.stdout.readline()
        if output_line:
            full_output += output_line
            output_text.insert(tk.END, output_line)

    # parse full_putput for duration
    p = re.compile('Duration: (\d+):(\d+):(\d+)')
    m = p.search(full_output)
    if m:
        hours = int(m.group(1))
        minutes = int(m.group(2))
        seconds = int(m.group(3))
        # duration in minutes
        duration = hours * 60 + minutes + seconds / 60
        output_text.insert(tk.END, f"Duration: {duration} minutes")
    
    # parse dimensions from full_output
    p = re.compile('Stream.+Video.+ (\d+)x(\d+)')
    m = p.search(full_output)
    if m:
        dimensions = (int(m.group(1)), int(m.group(2)))
        output_text.insert(tk.END, f"Dimensions: {dimensions[0]}x{dimensions[1]}")
    
    output_text.insert(tk.END, "Complete!")
    output_text.see(tk.END)

    return full_output, duration, dimensions



def process_queue():
    global queue_position
    if queue_position < len(queue):

        url, output_filename, size, duration, width, height, percentage = queue[queue_position]
        if percentage == 100:
            result_label.config(text=f"Skipping {output_filename} because it already exists.")
            queue_position += 1
            process_queue()
            return
        try:
            process = subprocess.Popen(['ffmpeg', '-nostdin', '-y', '-i', url, '-c', 'copy', output_filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

            threading.Thread(target=update_progress, args=(process, output_filename, duration), daemon=True).start()
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

    # close window when enter pressed
    modal_window.bind('<Return>', lambda event: add_to_queue())

def update_progress(process, output_filename, duration):
    global queue_position
    queue_row = queue[queue_position]

    while process.poll() is None:

        table_row = table_rows[queue_position+1]
        # Update output text area
        output_line = process.stdout.readline()
        if output_line:

            # parse line for size
            p = re.compile('size=\s*(\d+)kB')
            m = p.search(output_line)
            if m:
                kbs = int(m.group(1))
                if kbs > 0:
                    mbs = kbs / 1024
                    gbs = mbs / 1024
                    if gbs > 1:
                        queue_row[2] = f'{gbs:.2f} GB'
                    elif mbs > 1:
                        queue_row[2] = f'{mbs:.2f} MB'
                    else:
                        queue_row[2] = f'{kbs} KB'
                else:
                    queue_row[2] = f'0'

                update_list_entry_with_value(table_row[2], queue[queue_position][2])

            # parse line for time progress
            p = re.compile('time=-?(\d+):(\d+):(\d+)')
            m = p.search(output_line)
            if m:
                hours = int(m.group(1))
                minutes = int(m.group(2))
                seconds = int(m.group(3))
                # duration in minutes
                progress = hours * 60 + minutes + seconds / 60
                percent = progress / duration * 100
                queue_row[6] = percent

                update_list_entry_with_value(table_row[3], f'{percent:.1f}%')

            output_text.delete('1.0', tk.END)
            output_text.insert(tk.END, output_line)
            output_text.see(tk.END)
            queue_frame.update_idletasks()

    result_label.config(text=f"m3u8 file saved as {output_filename}")
    queue_row[6] = 100

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

create_queue_table()

clear_queue_button = tk.Button(right_middle_frame, text="Clear Queue", command=clear_queue)
clear_queue_button.grid(row=0, column=0, sticky=tk.E)
process_queue_button = tk.Button(right_middle_frame, text="Process Queue", command=process_queue)
process_queue_button.grid(row=0, column=1, sticky=tk.E)

# Result label
result_label = tk.Label(right_bottom_frame, text="")
result_label.grid(row=0, column=0, columnspan=2)

output_text = tk.Text(right_bottom_frame, wrap=tk.WORD, height=10)
output_text.grid(row=len(table_rows) + 1, columnspan=2, sticky='sew')

# Start the GUI event loop
window.mainloop()