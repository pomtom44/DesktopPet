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
from threading import Event, Thread
from tkinter import ttk
from PIL import Image
from urllib.request import urlretrieve
user = ctypes.windll.user32


#Static Variables
update_ver = 8
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
        
        #Create Menu
        self.menu = tk.Menu(self.window, tearoff=0)
        self.menu.add_command(label=menu_ver, command=lambda x=url_github: self.open_url(x))
        self.menu.add_command(label=menu_author, command=lambda x=url_github: self.open_url(x))
        self.menu.add_command(label="--------")
        self.menu.entryconfig("--------", state="disabled")
        self.menu.add_command(label="Random", command=lambda x="Random": self.change_pet(x))
        for filename in os.listdir('images'):
            if "_left" in filename:
                pet = filename.replace('_left.gif','')
                self.menu.add_command(label=pet, command=lambda x=pet: self.change_pet(x))
        self.menu.add_command(label="Quit", command=self.window.destroy)
        self.window.bind("<Button-3>", lambda event: self.menu.post(event.x_root, event.y_root))
        self.window.bind("<Button-1>", lambda event: self.jump())
        
        #Load Starting Image
        self.load_images()
        self.picker = "duck_left"
        self.frame_index = 0
        self.img = self.images["duck_left"][self.frame_index]
        self.timestamp = time.time()
        self.last_direction_change = time.time()
        self.dir = -1
        
        #Start Pet
        self.initialize_window()
        self.move_pet()
        self.window.mainloop()

    #Load images into Dictionary
    def load_images(self):
        for filename in os.listdir('images'):
            im = Image.open('images/' + filename)
            count = im.n_frames
            shortname = filename[:len(filename)-4]
            self.images[shortname] = [tk.PhotoImage(file='images/' + filename, format='gif -index %i' % i) for i in range(count)]
        
    #Custom attributes to add to class
    def addattr(self,x,val):
        self.__dict__[x]=val
        
    #Function to build window
    def initialize_window(self):
        self.window.config(background='black')
        self.window.wm_attributes('-transparentcolor', 'black')
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.label = tk.Label(self.window, bd=0, bg='black')
        self.x = 1040
        self.y = self.window.winfo_screenheight() - 126
        self.label.configure(image=self.img)
        self.label.pack()
        self.window.geometry('128x128+{}+{}'.format(self.x, self.y))

    #Function to load next image in GIF
    def change_frame(self, direction):
        if time.time() > self.timestamp + 0.05:
            self.timestamp = time.time()
            self.frame_index = (self.frame_index + 1)
            if self.frame_index >= len(direction):
                self.frame_index = 0
            self.img = direction[self.frame_index]
            
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

    #Main function to move pet (and other things)
    def move_pet(self):
    
        #Check if update
        if time.time() > (self.lastUpdateCheck + (autoUpdateTime * 60 * 60)):
            check_for_update()
            self.lastUpdateCheck = time.time()
    
        #Check if time to change direction
        if time.time() > (self.lastChange + self.changeTime):
            self.changeTime = random.randint(changeTimeMin, changeTimeMax)
            self.lastChange = time.time()
            #generate random number and see if direction should be changed - default to 50/50
            random_number = random.random()
            if random_number < 0.5:
                self.lastChange = time.time()
                #if pet is random then generate new pet on direction change
                if self.isRandom:
                    self.change_pet("Random")
                self.change_direction()

        #Move pet 1 pixel
        self.x = self.x + self.dir
        
        #Check if at edge of screen and change direction
        if self.x <= xmin or self.x >= (xmax - 128):
            self.change_direction()
        
        #Check if pet needs to re-adjust Y location based on monitor
        mons = monitor_areas()
        y = 0
        for mon in mons:
            if (mon[0]) <= (self.x + 64) <= (mon[2]):
                y = mon[3] - 126
        
        #Check if pet needs to jump
        if self.isJump == False:
            self.y = y
        if self.isJump == True:
            #Check if pet is jumping up
            if self.jumpDirection == 1:
                #Add 1 to jump location
                self.y = y - self.jumpHeight
                self.jumpHeight = self.jumpHeight + 1
                #if reached max height, change to falling mode
                if self.jumpHeight > jumpHeight:
                    self.jumpDirection = 0
            #check if pet is returning down
            if self.jumpDirection == 0:
                #Remove 1 from jump location
                self.y = y - self.jumpHeight
                self.jumpHeight = self.jumpHeight - 1
                #If back on ground then cancel jump
                if self.jumpHeight == 0:
                    self.jumpDirection = 1
                    self.isJump = False

        #Make sure correct gif is loaded
        if self.dir < 0:
            self.picker = self.picker.replace('right','left')
        else:
            self.picker = self.picker.replace('left','right')
            
        #Change Gif Frame
        pet = self.images[self.picker]
        self.change_frame(pet)

        #Rebuild image on screen
        self.window.geometry('128x128+{}+{}'.format(self.x, self.y))
        self.label.configure(image=self.img)
        self.label.pack()
        self.window.after(10, self.move_pet)
        self.window.lift()

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
    retval = []
    CBFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(RECT), ctypes.c_double)
    def cb(hMonitor, hdcMonitor, lprcMonitor, dwData):
        r = lprcMonitor.contents
        data = [hMonitor]
        data.append(r.dump())
        retval.append(data)
        return 1
    cbfunc = CBFUNC(cb)
    temp = user.EnumDisplayMonitors(0, 0, cbfunc, 0)
    return retval
def monitor_areas():
    retval = []
    monitors = get_monitors()
    for hMonitor, extents in monitors:
        data = [hMonitor]
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        mi.rcMonitor = RECT()
        mi.rcWork = RECT()
        res = user.GetMonitorInfoA(hMonitor, ctypes.byref(mi))
        data = mi.rcMonitor.dump()
        retval.append(data)
    return retval

#Function to check if pending update
def check_for_update():
    try:
        #Check for new update
        f = requests.get(url_version)
        newVer = int(f.text)
        doUpdate = False
        if newVer > update_ver:
            #If update, prompt to update
            result = ctypes.windll.user32.MessageBoxW(0, notice_update, "Update Avalibale", 4)
            #If approved then run update
            if result == 6:
                doUpdate = True                
    #Error if no internet / cant connect to server
    except:
        ctypes.windll.user32.MessageBoxW(0, error_noNetwork, "Error", 0)
    if doUpdate:
         #setup updater
        tk_1 = tk.Tk()
        tk_1.title("Updating")
        tk_1.geometry("300x50+50+50")
        text = tk.Label(tk_1, text="Launching Updater...", font=("Helvetica", 16))
        text.pack()
        tk_1.update()
        if not os.path.exists('temp'):
            os.mkdir('temp')
        shutil.copy('DesktopPet.exe', 'temp/DesktopPet.exe')
        time.sleep(1)
        open('temp/updating', 'a').close()
        tk_1.destroy
        os.startfile('temp\\DesktopPet.exe')
        sys.exit()


def updater():
    
    #Download Zip
    download('https://github.com/pomtom44/DesktopPet/releases/latest/download/DesktopPet.zip', 'temp/DesktopPet.zip')
    #Launch GUI
    tk_3 = tk.Tk()
    tk_3.title("Installing")
    tk_3.geometry("300x50+50+50")
    text = tk.Label(tk_3, text="Installing...", font=("Helvetica", 16))
    text.pack()
    tk_3.update()
    
    #Delete all files in root
    path = os.getcwd()
    
    files = os.listdir(path)
    for f in files:
        if f != "temp":
            try:
                shutil.rmtree(path + '/' + f)
            except:
                os.remove(path + '/' + f)
    
    #Extract Zip
    shutil.unpack_archive('temp/DesktopPet.zip','temp/extract')
    allfiles = os.listdir('temp/extract/DesktopPet')
    for f in allfiles:
        shutil.move(path + '\\temp\\extract\\DesktopPet\\' + f, path + '/' + f)
    
    tk_3.destroy
    os.startfile(path + '\\DesktopPet.exe')
    sys.exit()
    
    
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
    
#Main Script
if __name__ == "__main__":

    #Check if in update mode
    if os.path.exists('updating') or os.path.exists('temp\\updating') :
        updater()

    else:
        if os.path.exists('temp'):
            shutil.rmtree('temp')
        #Check if config exists and open
        try:
            with open('config.ini') as f:
                config = configparser.ConfigParser()
                config.read("config.ini")
                
                #Check if all options in config are set
                if not config.has_option('Variables', 'changeTimeMin'):
                    ctypes.windll.user32.MessageBoxW(0, error_corruptedConfig + "\nMissing changeTimeMin", "Error", 0)
                elif not config.has_option('Variables', 'changeTimeMax'):
                    ctypes.windll.user32.MessageBoxW(0, error_corruptedConfig + "\nMissing changeTimeMax", "Error", 0)
                elif not config.has_option('Variables', 'jumpHeight'):
                    ctypes.windll.user32.MessageBoxW(0, error_corruptedConfig + "\nMissing jumpHeight", "Error", 0)
                elif not config.has_option('Variables', 'autoUpdate'):
                    ctypes.windll.user32.MessageBoxW(0, error_corruptedConfig + "\nMissing autoUpdate", "Error", 0)
                elif not config.has_option('Variables', 'autoUpdateTime'):
                    ctypes.windll.user32.MessageBoxW(0, error_corruptedConfig + "\nMissing autoUpdateTime", "Error", 0)
                else:
                
                    #Load variables from Config
                    global changeTimeMin
                    changeTimeMin = int(config.get('Variables','changeTimeMin'))
                    global changeTimeMax
                    changeTimeMax = int(config.get('Variables','changeTimeMax'))
                    global jumpHeight
                    jumpHeight = int(config.get('Variables','jumpHeight'))
                    global autoUpdate
                    autoUpdate = bool(config.get('Variables','autoUpdate'))
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
                    
        #No Config, Throw error
        except IOError:
           ctypes.windll.user32.MessageBoxW(0, error_missingConfig, "Error", 0)
