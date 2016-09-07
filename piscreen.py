#!/usr/bin/env python3
import tkinter, mpd, configparser
from tkinter import Listbox, Label, N, S, E, W

root = tkinter.Tk()
root.geometry("320x240")
client = mpd.MPDClient(use_unicode=True)
footer_text = 'Some Footer!!'
config = configparser.ConfigParser()
config.read('config.ini')

class PiScreen(tkinter.Frame):

    def __init__(self, master: 'tkinter.Tk'):
        global client, footer_text
        client.connect("192.168.1.120", 6600)
        tkinter.Frame.__init__(self, master, padx=0, pady=0)
        self.pack()
        self.place(height=240, width=320, x=0, y=0)
        self.config(bg="black")
        self.queue = []
        self.playlists = []
        self.artists = []
        self.albums = []
        self.genres = []

        self.screen_data = {
            "1": ["QUEUE", "PLAYLISTS", "LIBRARY", "SETUP"],
            "1.1": {"ACTION": "QUEUE"},
            "1.2": {"ACTION": "PLAYLISTS"},
            "1.3": ["ARTISTS", "ALBUMS", "GENRES"],
            "1.3.1": {"ACTION": "ARTISTS"},
            "1.3.2": {"ACTION": "ALBUMS"},
            "1.3.3": {"ACTION": "GENRES"},
            "1.4": ["UPDATE LIBRARY", "CHANGE OUTPUT"],
            "1.4.1": {"ACTION": "UPDATE_LIBRARY"},
            "1.4.2": ["HDMI", "ANALOG", "USB"],
            "1.4.2.1": {"ACTION": "SET_HDMI_OUT"},
            "1.4.2.2": {"ACTION": "SET_ANALOG_OUT"},
            "1.4.2.3": {"ACTION": "SET_USB_OUT"}
        }

        self.screen_format = {
            "1.Q" : "SONG",
            # "1.A" : "ARTISTS",
            "1.P" : "PLAYLISTS"
        }

        self.headerText = 'SOME Header'
        self.headerTextVar = tkinter.StringVar()
        self.headerTextVar.set(str(self.headerText))
        # self.footerText = "Some Footer"
        self.footer_text_var = tkinter.StringVar()
        self.footer_text_var.set(str(footer_text))

        self.headerLabel = Label(self, font=('lucidatypewriter', 10, 'bold'), bg='grey', foreground='white', textvariable=self.headerTextVar)
        self.headerLabel.configure(width=320, height=1)
        self.headerLabel.pack(side = tkinter.TOP)

        self.listbox = Listbox(self, selectmode=tkinter.SINGLE, font=('lucidatypewriter', 10), bg='black',
                               fg='white', height=10, activestyle="none", borderwidth=0, highlightthickness=0)
        self.listbox.bind("<Key>", self.key)
        self.listbox.configure(width=320, height=10)
        self.listbox.pack(side = tkinter.TOP, expand = 1, ipadx = 0, ipady = 0, padx = 0, pady = 0)
        self.listbox.focus_set()

        self.footer = Label(self, textvariable=self.footer_text_var, font=('lucidatypewriter', 10, 'bold'), bg='grey',
                            foreground='black')
        self.footer.configure(width=320, height=1)
        self.footer.pack(side = tkinter.TOP)

        self.focus_set()
        self.bind("<Key>", self.key)
        self.screen = "1"
        self.show_screen()
        self.tick()

    def tick(self):
        self.update_header()
        self.after(500, self.tick)

    def show_screen(self):
        self.listbox.delete(0, self.listbox.size() - 1)
        format = "string";
        if self.screen in self.screen_format:
            format = self.screen_format[self.screen]
        if isinstance(self.screen_data[self.screen], list):
            for item in self.screen_data[self.screen]:
                if format == "string":
                    if not item:
                        self.listbox.insert(tkinter.END, "N/A")
                    else:
                        self.listbox.insert(tkinter.END, item)
                if format == "SONG":
                    self.listbox.insert(tkinter.END, item["artist"] + " - " + item["title"])

        self.listbox.select_set(0)  # This only sets focus on the first item.
        self.listbox.event_generate("<<ListboxSelect>>")
        # self.update()

    def update_header(self):
        status = client.status()
        header = ''
        if status["state"] == "play":
            song = client.currentsong()
            header = header + song["artist"] + "-" + song["title"] + " "
        header = header + "V"+status["volume"] + ",R" + status["random"]
        self.headerTextVar.set(header)

    def key(self, event):
        global footer_text, config
        # footer_text = "Some Data Entered!!"
        self.footer_text_var.set(str("Some Data Entered!!"))
        keycode = str(event.keycode)
        # self.footer.configure(text=str('Key Pressed ' + str(event.keycode)))
        if keycode == config["PISCREEN_KEYS"]["down"]:  # down
            if self.listbox.size() > 0:
                selection = int(self.listbox.curselection()[0])
                count = self.listbox.size()
                if selection < (count - 1):
                    self.listbox.select_clear(selection)
                    self.listbox.selection_set(selection + 1)
                    self.listbox.event_generate("<<ListboxSelect>>")
            return
        if keycode == config["PISCREEN_KEYS"]["up"]:  # up
            if self.listbox.size() > 0:
                selection = int(self.listbox.curselection()[0])
                count = self.listbox.size()
                if selection > 0:
                    self.listbox.select_clear(selection)
                    self.listbox.selection_set(selection - 1)
                    self.listbox.event_generate("<<ListboxSelect>>")
            return
        if keycode == config["PISCREEN_KEYS"]["left"] or keycode == config["PISCREEN_KEYS"]["back"]:  # left or escape
            if self.screen != "1":
                menu = self.screen.rsplit(".", maxsplit=1)
                new_screen = menu[0]
                self.screen = new_screen
                self.show_screen()
            return
        if keycode == config["PISCREEN_KEYS"]["right"] or keycode == config["PISCREEN_KEYS"]["ok"]:  # right or return
            if self.listbox.size() > 0:
                selection = int(self.listbox.curselection()[0]) + 1
                new_screen = self.screen + "." + str(selection)
                if new_screen in self.screen_data:
                    if type(self.screen_data[new_screen]) is list:
                        self.screen = new_screen
                        self.show_screen()
                    else:
                        self.run_command(self.screen_data[new_screen]["ACTION"])
                else:
                    if str(new_screen).startswith("1.Q."):
                        menu = new_screen.rsplit(".", maxsplit=1)
                        client.playid(int(self.queue[int(menu[1])-1]["id"]))
                print(self.screen)
            return
        print("pressed", repr(event.keycode))

    def run_command(self, action):
        global client
        if action == "QUEUE":
            print("QUEUE")
            queue = client.playlistinfo()
            self.queue.clear()
            for item in queue:
                self.queue.append(item)
            self.screen = "1.Q"
            self.screen_data["1.Q"] = self.queue
            self.show_screen()
        if action == "PLAYLISTS":
            print("PLAYLISTS")
        if action == "ARTISTS":
            print("ARTISTS")
            self.artists = client.list("artist")
            self.screen = "1.3.A"
            self.screen_data["1.3.A"] = self.artists
            self.show_screen()
        if action == "ALBUMS":
            print("ALBUMS")
            self.albums = client.list("album")
            self.screen = "1.3.B"
            self.screen_data["1.3.B"] = self.albums
            self.show_screen()
        if action == "GENRES":
            print("GENRES")
        if action == "UPDATE_LIBRARY":
            print("UPDATE_LIBRARY")
            client.rescan()

app = PiScreen(root)
app.mainloop()
