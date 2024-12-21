import os
import subprocess
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import threading
import time
import queue

class GNURadioGUI:
    def __init__(self, root):
        # Predefined flowgraphs for transmitter and receiver
        self.TRANSMIT_FLOWGRAPH = "/home/gnuradio/final/Transmit.py"  
        self.RECEIVE_FLOWGRAPH = "/home/gnuradio/final/Receive.py"
        self.LIVE_AUDIO_TX_FLOWGRAPH = "/home/gnuradio/final/WavfileTransmit.py"
        self.LIVE_AUDIO_RX_FLOWGRAPH = "/home/gnuradio/final/LiveAudioReceieve.py"
        self.LIVELIVE_AUDIO_TX_FLOWGRAPH = "/home/gnuradio/final/VoiceTransmit.py"

        self.root = root
        self.root.title("WAVE CONNECTORS")
        self.root.geometry("800x800")

        # Mode Selection Frame
        self.mode_frame = tk.LabelFrame(root, text="Select Operation Mode")
        self.mode_frame.pack(fill="x", padx=10, pady=5)

        self.mode_var = tk.StringVar(value="receive")
        self.receive_radio = tk.Radiobutton(self.mode_frame, text="Receive", variable=self.mode_var, value="receive", command=self.update_mode)
        self.receive_radio.pack(side=tk.LEFT, padx=10)
        self.transmit_radio = tk.Radiobutton(self.mode_frame, text="Transmit", variable=self.mode_var, value="transmit", command=self.update_mode)
        self.transmit_radio.pack(side=tk.LEFT, padx=10)
        self.live_audio_radio = tk.Radiobutton(self.mode_frame, text="Live Audio", variable=self.mode_var, value="live_audio", command=self.update_mode)
        self.live_audio_radio.pack(side=tk.LEFT, padx=10)

        # Live Audio Mode Frame
        self.live_audio_frame = tk.LabelFrame(root, text="Live Audio Settings")
        self.live_audio_mode_var = tk.StringVar(value="receive")
        self.live_audio_receive = tk.Radiobutton(self.live_audio_frame, text="Receive Audio", 
                                                variable=self.live_audio_mode_var, value="receive",
                                                command=self.update_live_audio_mode)
        self.live_audio_receive.pack(side=tk.LEFT, padx=10)
        self.live_audio_transmit = tk.Radiobutton(self.live_audio_frame, text="Transmit Recorded Audio", 
                                                 variable=self.live_audio_mode_var, value="transmit",
                                                 command=self.update_live_audio_mode)
        self.live_audio_transmit.pack(side=tk.LEFT, padx=10)
        self.new_audio_mode = tk.Radiobutton(self.live_audio_frame, text="Transmit Live Audio",
                                            variable=self.live_audio_mode_var, value="new_mode",
                                            command=self.update_live_audio_mode)
        self.new_audio_mode.pack(side=tk.LEFT, padx=10)


        # Live Audio File Selection Frame
        self.live_audio_file_frame = tk.LabelFrame(root, text="Live Audio File")
        self.live_audio_file_label = tk.Label(self.live_audio_file_frame, text="No audio file selected", anchor="w")
        self.live_audio_file_label.pack(side=tk.LEFT, expand=True, fill="x", padx=5)
        self.select_live_audio_button = tk.Button(self.live_audio_file_frame, text="Select Audio File", 
                                                 command=self.select_live_audio_file)
        self.select_live_audio_button.pack(side=tk.RIGHT, padx=5)

        # Input File Section (for Transmit mode)
        self.input_frame = tk.LabelFrame(root, text="Input File")
        self.input_frame.pack(fill="x", padx=10, pady=5)

        self.input_file_label = tk.Label(self.input_frame, text="No input file selected", anchor="w")
        self.input_file_label.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        self.select_input_button = tk.Button(self.input_frame, text="Select Input File", command=self.select_input_file)
        self.select_input_button.pack(side=tk.RIGHT, padx=5)

        # File Type Section (for Transmit mode)
        self.file_type_frame = tk.LabelFrame(root, text="File Type")
        self.file_type_frame.pack(fill="x", padx=10, pady=5)

        self.file_type_label = tk.Label(self.file_type_frame, text="File Type:")
        self.file_type_label.pack(side=tk.LEFT, padx=5)

        self.file_type_display = tk.Label(self.file_type_frame, text="")
        self.file_type_display.pack(side=tk.LEFT, padx=5)

        self.extension_label = tk.Label(self.file_type_frame, text="Extension:")
        self.extension_label.pack(side=tk.LEFT, padx=5)

        # Progress Section
        self.progress_frame = tk.Frame(root)
        self.progress_frame.pack(fill="x", padx=10, pady=5)

        self.progress_label = tk.Label(self.progress_frame, text="Wait:")
        self.progress_label.pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", length=500, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        # Action Button
        self.action_button = tk.Button(root, text="START", command=self.run_operation)
        self.action_button.pack(pady=5)

        # Console Output
        self.console = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10)
        self.console.pack(fill="both", expand=True, padx=10, pady=5)

        # State variables
        self.input_file = None
        self.live_audio_file = None
        self.is_running = False
        self.file_extension = None
        self.file_type = None
        self.process = None
        self.output_queue = queue.Queue()
        self.output_thread = None

        # Initial mode setup
        self.update_mode()

    def update_live_audio_mode(self):
        mode = self.live_audio_mode_var.get()
        if mode == "receive" or mode == "new_mode":
            self.live_audio_file_frame.pack_forget()
        else:
            self.live_audio_file_frame.pack(fill="x", padx=10, pady=5, after=self.live_audio_frame)

    def select_live_audio_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio Files", "*.wav *.mp3")]
        )
        
        if file_path:
            self.live_audio_file = file_path
            self.live_audio_file_label.config(text=f"Selected: {os.path.basename(file_path)}")
        else:
            self.live_audio_file = None
            self.live_audio_file_label.config(text="No audio file selected")

    def update_mode(self):
        mode = self.mode_var.get()
        
        # Hide all frames first
        self.input_frame.pack_forget()
        self.file_type_frame.pack_forget()
        self.progress_frame.pack_forget()
        self.live_audio_frame.pack_forget()
        self.live_audio_file_frame.pack_forget()
        
        if mode == "receive":
            self.action_button.config(text="START RECEIVING")
            self.progress_frame.pack(fill="x", padx=10, pady=5)
            
        elif mode == "transmit":
            self.input_frame.pack(fill="x", padx=10, pady=5)
            self.file_type_frame.pack(fill="x", padx=10, pady=5)
            self.progress_frame.pack(fill="x", padx=10, pady=5)
            self.action_button.config(text="SEND")
            
        elif mode == "live_audio":
            self.live_audio_frame.pack(fill="x", padx=10, pady=5)
            self.progress_frame.pack(fill="x", padx=10, pady=5)
            self.action_button.config(text="START LIVE AUDIO")
            self.update_live_audio_mode()  # Show/hide file selection based on live audio mode

    def select_input_file(self):
        # Only applicable in transmit mode
        if self.mode_var.get() != "transmit":
            return

        file_path = filedialog.askopenfilename(
            title="Select Input File", 
            filetypes=[("All Files", "*.*")]
        )
        
        if file_path:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            extension_to_type = {
                '.txt': 'Text',
                '.mp3': 'Audio',
                '.wav': 'Audio',
                '.jpg': 'Image',
                '.jpeg': 'Image',
                '.png': 'Image',
                '.mp4': 'Video',
                '.avi': 'Video',
                '.mkv': 'Video'
            }
            
            file_type = extension_to_type.get(file_extension, 'Unknown')
            
            self.file_type_display.config(text=file_type)
            self.extension_label.config(text=f"Extension: {file_extension}")
            
            self.input_file = file_path
            self.file_extension = file_extension
            self.file_type = file_type
            
            self.input_file_label.config(text=f"Selected: {os.path.basename(file_path)}")
        else:
            self.input_file = None
            self.file_extension = None
            self.file_type = None
            
            self.input_file_label.config(text="No input file selected")
            self.file_type_display.config(text="")
            self.extension_label.config(text="Extension:")


    def run_live_audio(self):
        def enqueue_output(out):
            for line in iter(out.readline, ''):
                self.output_queue.put(line)
            out.close()

        try:
            # Determine which flowgraph to use based on live audio mode
            mode = self.live_audio_mode_var.get()
            if mode == "receive":
                flowgraph = self.LIVE_AUDIO_RX_FLOWGRAPH
            elif mode == "transmit":
                flowgraph = self.LIVE_AUDIO_TX_FLOWGRAPH
            else:  # new_mode
                flowgraph = self.LIVELIVE_AUDIO_TX_FLOWGRAPH
            
            # Validate file selection for transmit mode
            if mode == "transmit" and not self.live_audio_file:
                raise Exception("Please select an audio file for transmission")
            
            # Create environment variables
            env = os.environ.copy()
            if mode == "transmit":
                env['AUDIO_FILE'] = self.live_audio_file
            
            # Run the appropriate flowgraph
            self.process = subprocess.Popen(
                ["python3", flowgraph],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )

            # Simulate progress
            for i in range(101):
                if not self.is_running:
                    self.process.terminate()
                    break
                self.progress_bar["value"] = i
                time.sleep(0.1)  # Simulated delay
            
            # Start output thread
            self.output_thread = threading.Thread(target=enqueue_output, args=(self.process.stdout,))
            self.output_thread.daemon = True
            self.output_thread.start()
            
            # Start checking output queue
            def check_output_queue():
                try:
                    while True:
                        try:
                            line = self.output_queue.get_nowait()
                            self.console.insert(tk.END, line)
                            self.console.see(tk.END)
                        except queue.Empty:
                            break
                    
                    if self.process and self.process.poll() is not None:
                        self.stop_operation()
                    else:
                        self.root.after(100, check_output_queue)
                except Exception as e:
                    self.console.insert(tk.END, f"Error in output processing: {str(e)}\n")
                    self.stop_operation()
            
            self.root.after(100, check_output_queue)
            self.is_running = True
            
        except Exception as e:
            self.console.insert(tk.END, f"Error: {str(e)}\n")
            self.stop_operation()

    def run_operation(self):
        # Validate inputs based on mode
        if self.mode_var.get() == "transmit" and not self.input_file:
            messagebox.showerror("Error", "No input file selected.")
            return
        elif (self.mode_var.get() == "live_audio" and 
              self.live_audio_mode_var.get() == "transmit" and 
              not self.live_audio_file):
            messagebox.showerror("Error", "No audio file selected.")
            return
        
        # Clear previous console output
        self.console.delete(1.0, tk.END)
        
        # Disable action button
        self.action_button.config(state=tk.DISABLED)
        
        # Reset progress
        self.progress_bar["value"] = 0
        
        

    
        # Receive mode function
        def run_receive_mode():
            def enqueue_output(out):
                for line in iter(out.readline, ''):
                    self.output_queue.put(line)
                out.close()

            def check_output_queue():
                try:
                    while True:
                        try:
                            line = self.output_queue.get_nowait()
                            self.console.insert(tk.END, line)
                            self.console.see(tk.END)
                        except queue.Empty:
                            break
                    
                    # Check if process is still running
                    if self.process and self.process.poll() is not None:
                        self.stop_operation()
                    else:
                        # Schedule next check
                        self.root.after(100, check_output_queue)
                except Exception as e:
                    self.console.insert(tk.END, f"Error in output processing: {str(e)}\n")
                    self.stop_operation()

            try:
                # Run the receive flowgraph
                self.process = subprocess.Popen(
                    ["python3", self.RECEIVE_FLOWGRAPH],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                for i in range(101):
                    if not self.is_running:
                        self.process.terminate()
                        break
                    self.progress_bar["value"] = i
                    time.sleep(0.1)  # Simulated delay
                
                # Start thread to read output
                self.output_thread = threading.Thread(target=enqueue_output, args=(self.process.stdout,))
                self.output_thread.daemon = True
                self.output_thread.start()
                
                # Start checking output queue
                self.root.after(100, check_output_queue)
                
                self.is_running = True
                
            except Exception as e:
                self.console.insert(tk.END, f"Error: {str(e)}\n")
                self.stop_operation()

        # Transmit mode function
        def run_transmit_mode():
            try:
                # Create environment variables for input and output files
                env = os.environ.copy()
                env['INPUT_FILE'] = self.input_file
                env['FILE_TYPE'] = self.file_type.lower() if self.file_type else ''
                env['FILE_EXTENSION'] = self.file_extension or ''
                
                # Run the transmit flowgraph
                self.process = subprocess.Popen(
                    ["python3", self.TRANSMIT_FLOWGRAPH],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env  # Pass environment variables
                )
                
                # Simulate progress (you'll want to replace this with actual progress tracking)
                for i in range(101):
                    if not self.is_running:
                        self.process.terminate()
                        break
                    self.progress_bar["value"] = i
                    time.sleep(0.1)  # Simulated delay
                
                # Capture output
                stdout, stderr = self.process.communicate()
                
                # Update console with output
                if stdout:
                    self.console.insert(tk.END, "Output:\n" + stdout + "\n")
                if stderr:
                    self.console.insert(tk.END, "Errors:\n" + stderr + "\n")
                
                # Mark process as complete
                self.progress_bar["value"] = 100
                
            except Exception as e:
                self.console.insert(tk.END, f"Error: {str(e)}\n")
            finally:
                self.stop_operation()

        # Start the appropriate mode thread
        self.is_running = True
        if self.mode_var.get() == "live_audio":
            threading.Thread(target=self.run_live_audio, daemon=True).start()
        elif self.mode_var.get() == "receive":
            threading.Thread(target=run_receive_mode, daemon=True).start()
        else:
            threading.Thread(target=run_transmit_mode, daemon=True).start()

    def stop_operation(self):
        # Stop the process if it's running
        if self.process:
            try:
                # Terminate the process
                self.process.terminate()
                
                # Wait for the process to actually end
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                self.process.kill()
            except Exception as e:
                self.console.insert(tk.END, f"Error stopping process: {str(e)}\n")
            
            # Reset process and threads
            self.process = None
            self.is_running = False

        # Reset UI
        self.action_button.config(state=tk.NORMAL)
        
        # Insert stop message
        self.console.insert(tk.END, "\n--- OPERATION STOPPED ---\n")
        self.console.see(tk.END)

    def on_closing(self):
        # Stop the process if it's running
        if self.is_running:
            self.stop_operation()
        self.root.destroy()

# Main application loop
if __name__ == "__main__":
    root = tk.Tk()
    app = GNURadioGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
