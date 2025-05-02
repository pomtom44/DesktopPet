import tkinter as tk
import time
import random
import ctypes
import os
import configparser
import requests
import webbrowser
import math
import shutil
import sys
import psutil
import shutil
import gc
import pkg_resources
import logging
from threading import Event, Thread
from tkinter import ttk
from PIL import Image
from urllib.request import urlretrieve
user = ctypes.windll.user32


#Static Variables
update_ver = 10
xmin = 0
xmax = 0
menu_ver = "Version: " + str(update_ver)
menu_author = "By Thomas Steel"
url_version = "https://raw.githubusercontent.com/pomtom44/DesktopPet/main/version"
url_github = "https://github.com/pomtom44/DesktopPet/"

#Display Messages
error_missingConfig = "Config file is missing\nPlease fix before running again"
error_corruptedConfig = "Config file is corrupted\nPlease fix before running again"
error_noNetwork = "Unable to check for downloads\nWe will try again later"
notice_update = "There is an update avalibale.\nWould you like to update?"


class Duck:

    def __init__(self):
        #Create Window
        self.window = tk.Tk()
        self.images = {}
        
        #Load Variables
        self.lastChange = time.time()
        self.changeTime = 10
        self.isRandom = False
        self.isJump = False
        self.jumpDirection = 1
        self.jumpHeight = 0
        self.lastUpdateCheck = time.time()
        
        #Window dimensions and position
        self.window_width = 128
        self.window_height = 128
        self.x = 1040  # Default x position
        self.y = 0     # Will be set in initialize_window
        
        #Cache monitor information
        self._cached_monitors = None
        self._last_monitor_check = 0
        self._monitor_refresh_interval = 600  # 10 minutes
        
        #Animation timing
        self._last_frame_time = time.time()
        self._frame_interval = 0.05  # 20 FPS
        self._last_move_time = time.time()
        self._move_interval = 0.01  # 100 FPS for movement
        
        #Create Menu
        self.menu = tk.Menu(self.window, tearoff=0)
        self.menu_items = {}
        
        #Add static menu items
        self.menu.add_command(label=menu_ver, command=lambda: self.open_url(url_github))
        self.menu.add_command(label=menu_author, command=lambda: self.open_url(url_github))
        self.menu.add_command(label="--------")
        self.menu.entryconfig("--------", state="disabled")
        
        #Add dynamic menu items
        self.menu.add_command(label="Random", command=lambda: self.change_pet("Random"))
        
        #Cache and add pet menu items
        for filename in os.listdir('images'):
            if "_left" in filename:
                pet = filename.replace('_left.gif','')
                self.menu_items[pet] = lambda p=pet: self.change_pet(p)
                self.menu.add_command(label=pet, command=self.menu_items[pet])
        
        self.menu.add_command(label="Quit", command=self.window.destroy)
        
        #Bind events
        self.window.bind("<Button-3>", self.show_menu)
        self.window.bind("<Button-1>", lambda e: self.jump())
        
        #Load Starting Image
        self.load_images()
        self.picker = "duck_left"
        self.frame_index = 0
        self.img = self.images["duck_left"][self.frame_index]
        self.dir = -1
        
        #Start Pet
        self.initialize_window()
        self.move_pet()
        self.window.mainloop()

    #Load images into Dictionary
    def load_images(self):
        try:
            for filename in os.listdir('images'):
                if not filename.endswith('.gif'):
                    continue
                try:
                    im = Image.open(f'images/{filename}')
                    count = im.n_frames
                    shortname = filename[:len(filename)-4]
                    self.images[shortname] = [
                        tk.PhotoImage(file=f'images/{filename}', format=f'gif -index {i}')
                        for i in range(count)
                    ]
                    im.close()  # Close the image file
                except Exception as e:
                    if getattr(sys, 'frozen', False):
                        ctypes.windll.user32.MessageBoxW(0, f"Warning: Could not load image {filename}: {e}", "Warning", 0)
        except Exception as e:
            if getattr(sys, 'frozen', False):
                ctypes.windll.user32.MessageBoxW(0, f"Error accessing images directory: {e}", "Error", 0)
            sys.exit(1)
        
    #Custom attributes to add to class
    def addattr(self,x,val):
        self.__dict__[x]=val
        
    #Function to build window
    def initialize_window(self):
        """Initialize the window with proper positioning."""
        self.window.config(background='black')
        self.window.wm_attributes('-transparentcolor', 'black')
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        
        #Create label
        self.label = tk.Label(self.window, bd=0, bg='black')
        self.label.configure(image=self.img)
        self.label.pack()
        
        #Get initial position
        monitor = self.get_current_monitor()
        if monitor:
            self.x = monitor[2] - self.window_width  # Start at right edge
            self.y = monitor[3] - 126  # Align with bottom
        else:
            # Fallback to default position
            self.y = self.window.winfo_screenheight() - 126
            
        #Set window geometry
        self.window.geometry(f'{self.window_width}x{self.window_height}+{self.x}+{self.y}')
        
        # Disable window updates during movement
        self.window.update_idletasks()

    #Function to load next image in GIF
    def change_frame(self, direction):
        current_time = time.time()
        if current_time - self._last_frame_time >= self._frame_interval:
            self._last_frame_time = current_time
            self.frame_index = (self.frame_index + 1) % len(direction)
            self.img = direction[self.frame_index]
            self.label.configure(image=self.img)
            
    #Function to change pet GIF
    def change_pet(self,pet):
        #If pet is random, then pick a random pet
        if pet == "Random":
            self.isRandom = True
            isSet = False
            while not isSet:
                pet = random.choice(list(self.images))
                #Make sure pet direction is correct
                if self.dir < 0:
                    if "_left" in pet:
                        self.picker = pet
                        isSet = True
                else:
                    if "_right" in pet:
                        self.picker = pet
                        isSet = True 
        #If not random then pick selected pet
        else:
            self.isRandom = False
            self.picker = pet
            if self.dir < 0:
                if "_left" in self.picker:
                    null = False
                elif "_right" in self.picker:
                    self.picker = self.picker.replace('right','left')
                else:
                    self.picker = self.picker + "_left"
            else:
                if "_right" in self.picker:
                    null = False
                elif "_left" in self.picker:
                    self.picker = self.picker.replace('left','right')
                else:
                    self.picker = self.picker + "_right"
    
    #Function to change direction
    def change_direction(self):
        self.dir = -self.dir
    
    #Function for jump action
    def jump(self):
        if self.isJump == False:
            self.isJump = True
            
    #Function to open URL
    def open_url(self, url):
        webbrowser.open(url)

    def show_menu(self, event):
        """Show the context menu at the current mouse position."""
        self.menu.post(event.x_root, event.y_root)

    #Main function to move pet (and other things)
    def move_pet(self):
        current_time = time.time()
        
        # Cache monitor areas to avoid repeated calls
        if not hasattr(self, '_cached_monitors') or current_time - self._last_monitor_check > self._monitor_refresh_interval:
            self._cached_monitors = monitor_areas()
            self._last_monitor_check = current_time
    
        #Check if update (only check every 30 minutes)
        if current_time > (self.lastUpdateCheck + (autoUpdateTime * 60 * 60)):
            check_for_update()
            self.lastUpdateCheck = current_time
    
        #Check if time to change direction
        if current_time > (self.lastChange + self.changeTime):
            self.changeTime = random.randint(changeTimeMin, changeTimeMax)
            self.lastChange = current_time
            if random.random() < 0.5:
                if self.isRandom:
                    self.change_pet("Random")
                self.change_direction()

        #Move pet 1 pixel
        self.x = self.x + self.dir
        
        #Check if at edge of screen and change direction
        if self.x <= xmin or self.x >= (xmax - 128):
            self.change_direction()
        
        #Check if pet needs to re-adjust Y location based on monitor
        mons = self._cached_monitors
        y = 0
        for mon in mons:
            if (mon[0]) <= (self.x + 64) <= (mon[2]):
                y = mon[3] - 126
        
        #Optimized jump calculations
        if self.isJump:
            self.y = y - self.jumpHeight
            self.jumpHeight += self.jumpDirection
            if self.jumpHeight > jumpHeight:
                self.jumpDirection = -1
            elif self.jumpHeight <= 0:
                self.jumpDirection = 1
                self.isJump = False
                self.jumpHeight = 0
        else:
            self.y = y

        #Update direction and frame
        self.picker = self.picker.replace('right','left') if self.dir < 0 else self.picker.replace('left','right')
        self.change_frame(self.images[self.picker])

        #Update window position
        self.window.geometry('128x128+{}+{}'.format(self.x, self.y))
        
        # Schedule next move with optimized timing
        next_move = max(0, self._move_interval - (time.time() - current_time))
        self.window.after(int(next_move * 1000), self.move_pet)
        
        # Only lift window if it's not already on top
        if not self.window.attributes('-topmost'):
            self.window.lift()

    def get_current_monitor(self):
        """Get the current monitor information with caching."""
        current_time = time.time()
        if (self._cached_monitors is None or 
            current_time - self._last_monitor_check > self._monitor_refresh_interval):
            self._cached_monitors = monitor_areas()
            self._last_monitor_check = current_time
        
        if not self._cached_monitors:
            return None
            
        #Find the monitor that contains the pet's center
        pet_center = self.x + (self.window_width // 2)
        for mon in self._cached_monitors:
            if mon[0] <= pet_center <= mon[2]:
                return mon
        return self._cached_monitors[0]

#Classes used to get monitor information
class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]
    
    def dump(self):
        return [int(val) for val in (self.left, self.top, self.right, self.bottom)]

class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_ulong),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', ctypes.c_ulong)
    ]

def get_monitors():
    """Get all monitor information with error handling."""
    retval = []
    CBFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(RECT), ctypes.c_double)
    
    def cb(hMonitor, hdcMonitor, lprcMonitor, dwData):
        try:
            r = lprcMonitor.contents
            data = [hMonitor]
            data.append(r.dump())
            retval.append(data)
            return 1
        except Exception as e:
            print(f"Error getting monitor info: {e}")
            return 0
            
    cbfunc = CBFUNC(cb)
    try:
        user.EnumDisplayMonitors(0, 0, cbfunc, 0)
    except Exception as e:
        print(f"Error enumerating monitors: {e}")
    return retval

def monitor_areas():
    """Get monitor areas with caching and error handling."""
    retval = []
    try:
        monitors = get_monitors()
        for hMonitor, extents in monitors:
            try:
                mi = MONITORINFO()
                mi.cbSize = ctypes.sizeof(MONITORINFO)
                mi.rcMonitor = RECT()
                mi.rcWork = RECT()
                res = user.GetMonitorInfoA(hMonitor, ctypes.byref(mi))
                if res:
                    data = mi.rcMonitor.dump()
                    retval.append(data)
            except Exception as e:
                print(f"Error getting monitor info for monitor {hMonitor}: {e}")
    except Exception as e:
        print(f"Error in monitor_areas: {e}")
    return retval

def start_update():
    """Start the update process with proper error handling."""
    try:
        print("Starting update process...")
        # Get the correct directory based on whether we're running as a script or executable
        if getattr(sys, 'frozen', False):
            current_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
        print(f"Current directory: {current_dir}")
        
        # Create update flag with status 1
        update_flag = os.path.join(current_dir, 'updating')
        with open(update_flag, 'w') as f:
            f.write('1')
            
        # Copy current executable as updater
        current_exe = os.path.join(current_dir, 'DesktopPet.exe')
        updater_exe = os.path.join(current_dir, 'DesktopPetUpdater.exe')
        
        if os.path.exists(current_exe):
            print(f"Creating updater at {updater_exe}")
            shutil.copy2(current_exe, updater_exe)
            
            # Launch updater
            print(f"Launching updater from {updater_exe}")
            os.startfile(updater_exe)
            sys.exit()
        else:
            raise FileNotFoundError(f"Could not find {current_exe}")
            
    except Exception as e:
        print(f"Error starting update: {e}")
        ctypes.windll.user32.MessageBoxW(0, f"Update failed: {str(e)}", "Error", 0)
        sys.exit(1)

def updater():
    """Handle the update process with progress feedback and cleanup."""
    try:
        print("Updater started...")
        # Get the correct directory based on whether we're running as a script or executable
        if getattr(sys, 'frozen', False):
            current_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
        print(f"Current directory: {current_dir}")
        
        # Check update status
        update_flag = os.path.join(current_dir, 'updating')
        if not os.path.exists(update_flag):
            print("No update in progress, exiting...")
            return
            
        with open(update_flag, 'r') as f:
            status = f.read().strip()
            
        if status == '1':
            print("Status 1: Downloading new version...")
            # Show progress window
            progress_window = tk.Tk()
            progress_window.title("Updating DesktopPet")
            progress_window.geometry("400x150")
            progress_window.resizable(False, False)
            
            # Center the window
            screen_width = progress_window.winfo_screenwidth()
            screen_height = progress_window.winfo_screenheight()
            x = (screen_width - 400) // 2
            y = (screen_height - 150) // 2
            progress_window.geometry(f"400x150+{x}+{y}")
            
            # Create progress bar
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_window, length=350, mode='determinate', variable=progress_var)
            progress_bar.pack(pady=20)
            
            # Create status label
            status_label = tk.Label(progress_window, text="Downloading update...", font=("Arial", 10))
            status_label.pack(pady=10)
            
            def update_progress(percent, message):
                progress_var.set(percent)
                status_label.config(text=message)
                progress_window.update()
            
            # Download update
            try:
                # Download the executable directly
                current_exe = os.path.join(current_dir, 'DesktopPet.exe')
                download('https://github.com/pomtom44/DesktopPet/releases/latest/download/DesktopPet.exe', current_exe)
                update_progress(100, "Download complete!")
                print("Download complete")
            except Exception as e:
                raise Exception(f"Download failed: {str(e)}")
            
            # Update status to 2
            with open(update_flag, 'w') as f:
                f.write('2')
            
            # Close progress window
            progress_window.destroy()
            
            # Launch new version
            print("Launching new version...")
            os.startfile(current_exe)
            sys.exit()
            
        elif status == '2':
            print("Status 2: Cleaning up...")
            # Clean up update flag
            if os.path.exists(update_flag):
                os.remove(update_flag)
            
            # Clean up updater
            updater_exe = os.path.join(current_dir, 'DesktopPetUpdater.exe')
            if os.path.exists(updater_exe):
                os.remove(updater_exe)
            
            print("Cleanup complete")
            return
            
    except Exception as e:
        print(f"Error during update: {e}")
        error_message = f"Update failed: {str(e)}\n\nPlease try updating manually from the GitHub repository."
        ctypes.windll.user32.MessageBoxW(0, error_message, "Update Error", 0)
        sys.exit(1)

def check_for_update():
    """Check for updates and handle the update process."""
    try:
        # Skip update check if updating file exists
        update_flag = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'updating')
        if os.path.exists(update_flag):
            print("Update in progress, skipping update check...")
            return
            
        print("Checking for updates...")
        #Check for new update
        response = requests.get(url_version, timeout=5)
        response.raise_for_status()
        newVer = int(response.text)
        print(f"Current version: {update_ver}, Server version: {newVer}")
        
        if newVer > update_ver:
            print("Update available!")
            #If update, prompt to update
            result = ctypes.windll.user32.MessageBoxW(0, notice_update, "Update Available", 4)
            #If approved then run update
            if result == 6:
                print("User approved update, starting update process...")
                start_update()
            else:
                print("User declined update")
        else:
            print("No update available")
    except requests.RequestException as e:
        print(f"Network error during update check: {e}")
        ctypes.windll.user32.MessageBoxW(0, error_noNetwork, "Error", 0)
    except ValueError as e:
        print(f"Invalid version number received: {e}")
    except Exception as e:
        print(f"Unexpected error during update check: {e}")

#Download File with Progress Bar
def download(url, filename):
    tk_2 = progressbar = quit_id = None
    ready = Event()
    def reporthook(blocknum, blocksize, totalsize):
        nonlocal quit_id
        if blocknum == 0: # started downloading
            def guiloop():
                nonlocal tk_2, progressbar
                tk_2 = tk.Tk()
                tk_2.withdraw() # hide
                progressbar = ttk.Progressbar(tk_2, length=400)
                progressbar.grid()
                # show progress bar if the download takes more than .5 seconds
                tk_2.after(500, tk_2.deiconify)
                ready.set() # gui is ready
                tk_2.mainloop()
            Thread(target=guiloop).start()
        ready.wait(1) # wait until gui is ready
        percent = (blocknum * blocksize * 1e2 / totalsize) # assume totalsize > 0
        if quit_id is None:
            tk_2.title('Downloading %%%.0f' % (percent))
            progressbar['value'] = percent # report progress
            if percent >= 100:  # finishing download
                quit_id = tk_2.after(1000, tk_2.quit) # close GUI
    return urlretrieve(url, filename, reporthook)
    
def extract_images():
    """Extract bundled images to the images folder."""
    try:
        if not os.path.exists('images'):
            print("Extracting images...")
            os.makedirs('images', exist_ok=True)
            
            # Get the path to the bundled images
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                base_path = sys._MEIPASS
            else:
                # Running as script
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            # Copy all images from the bundled folder
            bundled_images_path = os.path.join(base_path, 'images')
            if os.path.exists(bundled_images_path):
                for filename in os.listdir(bundled_images_path):
                    if filename.endswith('.gif'):
                        src = os.path.join(bundled_images_path, filename)
                        dst = os.path.join('images', filename)
                        shutil.copy2(src, dst)
                print("Images extracted successfully.")
            else:
                print("Warning: Bundled images not found.")
    except Exception as e:
        print(f"Error extracting images: {e}")
        ctypes.windll.user32.MessageBoxW(0, "Failed to extract images. The application may not work correctly.", "Warning", 0)

def extract_config():
    """Extract bundled config file to the root directory."""
    try:
        if not os.path.exists('config.ini'):
            print("Extracting config file...")
            
            # Get the path to the bundled config
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                base_path = sys._MEIPASS
            else:
                # Running as script
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            # Copy config from the bundled folder
            bundled_config_path = os.path.join(base_path, 'config.ini')
            if os.path.exists(bundled_config_path):
                shutil.copy2(bundled_config_path, 'config.ini')
                print("Config file extracted successfully.")
            else:
                print("Warning: Bundled config not found, creating default config...")
                create_default_config()
    except Exception as e:
        print(f"Error extracting config: {e}")
        print("Creating default config...")
        create_default_config()

def create_default_config():
    """Create a default config file."""
    try:
        default_config = """[Variables]

;Auto Updater Settings
;Check time in Hours
autoUpdate: True
autoUpdateTime: 4

;Number of seconds for min and max for the random direction changer
changeTimeMin: 10
changeTimeMax: 30

;Jump Settings
jumpHeight: 20"""
        
        with open('config.ini', 'w') as configfile:
            configfile.write(default_config)
        print("Default configuration file created.")
    except Exception as e:
        print(f"Error creating default config: {e}")
        ctypes.windll.user32.MessageBoxW(0, "Failed to create config file. The application may not work correctly.", "Warning", 0)

# Set up logging
def setup_logging():
    try:
        # Configure logging to only show errors in console
        logging.basicConfig(
            level=logging.ERROR,
            format='%(levelname)s - %(message)s'
        )
        return True
    except Exception as e:
        if getattr(sys, 'frozen', False):
            ctypes.windll.user32.MessageBoxW(0, f"Failed to setup logging: {e}", "Error", 0)
        return False

def read_update_status(update_flag):
    """Try to read the update status with retries."""
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            if not os.path.exists(update_flag):
                return None
                
            with open(update_flag, 'r') as f:
                return f.read().strip()
        except Exception as e:
            if attempt == max_retries - 1:
                if getattr(sys, 'frozen', False):
                    ctypes.windll.user32.MessageBoxW(0, 
                        f"Failed to read update status. The file may be locked by another process.\n\nError: {e}", 
                        "Update Error", 0)
                return None
            time.sleep(retry_delay)
    return None

def remove_update_flag(update_flag):
    """Try to remove the update flag with retries."""
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            if os.path.exists(update_flag):
                os.remove(update_flag)
                return True
        except Exception as e:
            if attempt == max_retries - 1:
                if getattr(sys, 'frozen', False):
                    ctypes.windll.user32.MessageBoxW(0, 
                        f"Failed to remove update flag. The file may be locked by another process.\n\nError: {e}", 
                        "Update Error", 0)
                return False
            time.sleep(retry_delay)
    return False

#Main Script
if __name__ == "__main__":
    setup_logging()
    
    # Extract images and config on first run
    extract_images()
    extract_config()
    
    #Get current directory
    if getattr(sys, 'frozen', False):
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
    
    #Check if in update mode
    update_flag = os.path.join(current_dir, 'updating')
    should_run_updater = False
    
    if os.path.exists(update_flag):
        status = read_update_status(update_flag)
        
        if status is not None:
            if status == '2':
                try:
                    # Clean up update flag
                    if remove_update_flag(update_flag):
                        pass
                    
                    # Clean up updater
                    updater_exe = os.path.join(current_dir, 'DesktopPetUpdater.exe')
                    if os.path.exists(updater_exe):
                        try:
                            os.remove(updater_exe)
                        except Exception as e:
                            if getattr(sys, 'frozen', False):
                                ctypes.windll.user32.MessageBoxW(0, 
                                    f"Failed to remove updater executable. You may need to remove it manually.\n\nError: {e}", 
                                    "Update Error", 0)
                except Exception as e:
                    if getattr(sys, 'frozen', False):
                        ctypes.windll.user32.MessageBoxW(0, f"Error during cleanup: {e}", "Update Error", 0)
            else:
                should_run_updater = True
        else:
            # If we couldn't read the status, try to remove the flag and continue
            remove_update_flag(update_flag)
    
    # Check if we should run the updater
    current_exe = os.path.basename(sys.executable if getattr(sys, 'frozen', False) else __file__)
    
    if should_run_updater or current_exe.lower() == 'desktoppetupdater.exe':
        updater()
    else:
        # Normal startup path
        try:
            config = configparser.ConfigParser()
            config.read("config.ini")
            
            #Required configuration options
            required_options = {
                'Variables': ['changeTimeMin', 'changeTimeMax', 'jumpHeight', 
                            'autoUpdate', 'autoUpdateTime']
            }
            
            #Validate configuration
            for section, options in required_options.items():
                if not config.has_section(section):
                    raise ValueError(f"Missing section: {section}")
                for option in options:
                    if not config.has_option(section, option):
                        raise ValueError(f"Missing option: {option} in section {section}")
            
            #Load variables from Config
            global changeTimeMin
            changeTimeMin = int(config.get('Variables','changeTimeMin'))
            global changeTimeMax
            changeTimeMax = int(config.get('Variables','changeTimeMax'))
            global jumpHeight
            jumpHeight = int(config.get('Variables','jumpHeight'))
            global autoUpdate
            autoUpdate = config.getboolean('Variables','autoUpdate')
            global autoUpdateTime
            autoUpdateTime = int(config.get('Variables','autoUpdateTime'))
            
            #Configure Monitor sizes
            mons = monitor_areas()
            for mon in mons:
                if mon[0] > xmax:
                    xmax = mon[0]
                if mon[0] < xmin:
                    xmin = mon[0]     
                if mon[2] > xmax:
                    xmax = mon[2]
                if mon[2] < xmin:
                    xmin = mon[2]
            
            #Initial Update Check
            if autoUpdate:
                check_for_update()
            
            #Launch
            Duck()
            
        except ValueError as e:
            ctypes.windll.user32.MessageBoxW(0, f"{error_corruptedConfig}\n{str(e)}", "Error", 0)
        except Exception as e:
            ctypes.windll.user32.MessageBoxW(0, f"Unexpected error: {str(e)}", "Error", 0)