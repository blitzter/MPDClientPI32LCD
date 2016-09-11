#!/usr/bin/env python3
import tkinter, mpd, configparser, subprocess, sys
from tkinter import Listbox, Label, Canvas, Frame, Y, X
from PIL import Image, ImageTk

root = tkinter.Tk()
root.geometry("320x240")
client = mpd.MPDClient(use_unicode=True)
footer_text = 'Some Footer!!'
config = configparser.ConfigParser()
config.read('config.ini')

status = {}

queue = []
playlists = []
artists = []
albums = []
genres = []
songs = []

selectedAlbum = ''
selectedArtist = ''
selectedGenre = ''
currentSong = None

keyMode = 'MENU'
textEntry = ''
textBackAction = ''
textSaveAction = ''

image = None
tickCount = 0


class PiScreen(tkinter.Frame):

    def __init__(self, master: 'tkinter.Tk'):
        global client, status, footer_text
        client.connect("192.168.1.120", 6600)
        tkinter.Frame.__init__(self, master, padx=0, pady=0)
        self.pack()
        self.place(height=240, width=320, x=0, y=0)
        self.config(bg="black")
        status = client.status()
        self.volume = int(status["volume"])

        self.screen_data = {
            "1": ["QUEUE", "PLAYLISTS", "LIBRARY", "SETUP", "CLEAR PLAYLIST", "RANDOM "+status['random'], "REPEAT "+status['repeat'], "SINGLE "+status['single'], "CONSUME "+status['consume']],
            "1.1": {"ACTION": "QUEUE"},
            "1.2": {"ACTION": "PLAYLISTS"},
            "1.3": ["ARTISTS", "ALBUMS", "GENRES"],
            "1.3.1": {"ACTION": "ARTISTS"},
            "1.3.2": {"ACTION": "ALBUMS"},
            "1.3.3": {"ACTION": "GENRES"},
            "1.4": ["UPDATE LIBRARY", "RANDOM_MODE","CHANGE OUTPUT"],
            "1.4.1": {"ACTION": "UPDATE_LIBRARY"},
            "1.4.2": {"ACTION": "RANDOM_MODE"},
            "1.4.3": ["HDMI", "ANALOG", "USB"],
            "1.4.3.1": {"ACTION": "SET_HDMI_OUT"},
            "1.4.3.2": {"ACTION": "SET_ANALOG_OUT"},
            "1.4.3.3": {"ACTION": "SET_USB_OUT"},
            "1.5": {"ACTION": "CLEAR"},
            "1.6": {"ACTION": "RANDOM"},
            "1.7": {"ACTION": "REPEAT"},
            "1.8": {"ACTION": "SINGLE"},
            "1.9": {"ACTION": "CONSUME"}
        }

        self.screen_format = {
            "1.Q": "SONG",
            "1.P": "PLAYLIST"
        }

        self.headerText = 'SOME Header'
        self.headerTextVar = tkinter.StringVar()
        self.headerTextVar.set(str(self.headerText))
        self.footer_text_var = tkinter.StringVar()
        self.footer_text_var.set(str(footer_text))

        self.headerFrame = Frame(self, width=320, height=20, bg="black")
        self.headerFrame.pack(side=tkinter.TOP, fill=X)

        self.headerLabel = Label(self.headerFrame, font=('lucidatypewriter', 10, 'bold'), bg='black', foreground='white', textvariable=self.headerTextVar, justify=tkinter.LEFT, anchor=tkinter.W)
        self.headerLabel.place(x=0, y=0, width=300, height=20, anchor=tkinter.NW)

        self.volumeLabel = Label(self.headerFrame, font=('lucidatypewriter', 10, 'bold'), bg='black', foreground='white', text='')
        self.volumeLabel.place(x=300, y=0, anchor=tkinter.NW)

        self.mainFrame = Frame(self, width=320, height=200)
        self.mainFrame.pack(side=tkinter.TOP, fill=Y)

        self.listbox = Listbox(self.mainFrame, selectmode=tkinter.SINGLE, font=('lucidatypewriter', 10), bg='black',
                               fg='white', height=10, activestyle="none", borderwidth=0, highlightthickness=0)
        self.listbox.bind("<Key>", self.key)
        self.listbox.configure(width=320, height=11)
        self.listbox.pack(side=tkinter.TOP, expand=1, ipadx=0, ipady=0, padx=0, pady=0)
        self.listbox.focus_set()

        self.player = Canvas(self.mainFrame, width=320, height=200, bg="black", borderwidth=0, highlightthickness=0)

        self.footer = Label(self, textvariable=self.footer_text_var, font=('lucidatypewriter', 10, 'bold'), bg='black',
                            foreground='white')
        self.footer.configure(width=320, height=1)
        self.footer.pack(side = tkinter.BOTTOM)

        self.focus_set()
        self.bind("<Key>", self.key)
        self.screen = "1"
        self.show_screen()
        self.tick()

    def tick(self):
        global tickCount, keyMode
        self.update_header()
        if keyMode != 'PLAYER':
            tickCount += 1
            if tickCount > 120:
                tickCount = 0
                self.screen = ''
                self.show_screen()
        else:
            tickCount = 0
        self.after(500, self.tick)

    def update_header(self):
        global status, keyMode, currentSong
        status = client.status()
        self.volume = int(status["volume"])
        header = ''
        if status["state"] == "play":
            currentSong = client.currentsong()
            header = header + currentSong["artist"][:15] + "-" + currentSong["title"][:25]
        # header = header + "V" + status["volume"] + ",R" + status["random"]
        self.volumeLabel.configure(text=status["volume"])
        if self.headerTextVar.get() != header:
            self.headerTextVar.set(header)
            if keyMode == 'PLAYER':
                self.show_player()

    def show_screen(self):
        global keyMode
        if self.screen == '':
            keyMode = 'PLAYER'
            self.listbox.pack_forget()
            self.player.pack(side=tkinter.TOP, expand=1, ipadx=0, ipady=0, padx=0, pady=0)
            self.show_player()
            self.update()
            self.screen = '1'
            return
        self.listbox.delete(0, self.listbox.size() - 1)
        format = "string"
        if self.screen in self.screen_format:
            format = self.screen_format[self.screen]
        if isinstance(self.screen_data[self.screen], list):
            for item in self.screen_data[self.screen]:
                if format == "string":
                    if not item:
                        self.listbox.insert(tkinter.END, "N/A")
                    else:
                        self.listbox.insert(tkinter.END, item[:45])
                if format == "SONG":
                    songname = ''
                    if 'artist' in item:
                        songname = item['artist'][:20]
                    songname += " - "
                    if 'title' in item:
                        songname += item['title'][:25]
                    self.listbox.insert(tkinter.END, songname)
                if format == "PLAYLIST":
                    playlistname = ''
                    if isinstance(item, str):
                        playlistname = item
                    else:
                        playlistname = item['playlist']
                    self.listbox.insert(tkinter.END, playlistname)

        self.listbox.select_set(0)  # This only sets focus on the first item.
        self.listbox.event_generate("<<ListboxSelect>>")
        self.update()
        return

    def show_player(self):
        global image, status, currentSong
        if sys.platform.startswith('linux'):
            process = subprocess.Popen("./coverart.sh", shell=True, stdout=subprocess.PIPE).stdout.read()
        else:
            process = "./icons/ic_album_white_48dp.png"
        image = ImageTk.PhotoImage(Image.open(process).resize((150,150), Image.ANTIALIAS))
        self.player.create_image(75, 75, image=image)
        if status["state"] == "play":
            self.player.create_rectangle(151, 1, 320, 150, fill="black")
            self.player.create_text(152, 4, text="Artist:", anchor=tkinter.NW, fill="grey",
                                    font=('lucidatypewriter', 10, 'bold'))
            self.player.create_text(152, 20, text=currentSong['artist'], anchor=tkinter.NW, fill="white",
                                    font=('lucidatypewriter', 10, 'bold'))
            self.player.create_text(152, 36, text="Song:", anchor=tkinter.NW, fill="grey",
                                    font=('lucidatypewriter', 10, 'bold'))
            self.player.create_text(152, 52, text=currentSong['title'], anchor=tkinter.NW, fill="white",
                                    font=('lucidatypewriter', 10, 'bold'))
            self.player.create_text(152, 68, text="Album:", anchor=tkinter.NW, fill="grey",
                                    font=('lucidatypewriter', 10, 'bold'))
            self.player.create_text(152, 84, text=currentSong['album'], anchor=tkinter.NW, fill="white",
                                    font=('lucidatypewriter', 10, 'bold'))
        else:
            self.player.create_rectangle(151, 1, 320, 150, fill="black")
            self.player.create_text(152, 4, text="Not Playing", anchor=tkinter.NW, fill="grey",
                                    font=('lucidatypewriter', 10, 'bold'))
        return

    def key(self, event):
        global config, client, selectedAlbum, selectedArtist, selectedGenre
        global keyMode, textEntry, textBackAction, textSaveAction, tickCount
        global albums, artists, queue, songs, playlists, status, genres

        tickCount = 0
        keycode = str(event.keycode)
        # self.footer_text_var.set(str("Key Pressed : "+keycode))
        if keyMode == 'PLAYER' and keycode != config["PISCREEN_KEYS"]["vol_up"] \
                and keycode != config["PISCREEN_KEYS"]["vol_down"]  \
                and keycode != config["PISCREEN_KEYS"]["play"]  \
                and keycode != config["PISCREEN_KEYS"]["next"]  \
                and keycode != config["PISCREEN_KEYS"]["prev"] :
            self.listbox.pack(side = tkinter.TOP, expand = 1, ipadx = 0, ipady = 0, padx = 0, pady = 0)
            keyMode = 'MENU'
            self.player.pack_forget()
            self.show_screen()
            self.update()
            return
        if keyMode == 'TEXT':
            if keycode == config["PISCREEN_KEYS"]["back"]:  # back
                keyMode = 'MENU'
                self.run_command(textBackAction)
            if keycode == config["PISCREEN_KEYS"]["ok"]: # ok
                keyMode = 'MENU'
                self.run_command(textSaveAction)
            if event.keysym in '0123456789-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
                textEntry += event.keysym
                self.footer_text_var.set(str("Entry : " + textEntry))
            return
        # self.footer.configure(text=str('Key Pressed ' + str(event.keycode)))
        if keycode == config["PISCREEN_KEYS"]["menu"]:
            if self.screen == "1.P":
                selection = int(self.listbox.curselection()[0]) + 1
                if selection > 1:
                    self.footer_text_var.set(str("Press 1 + OK to Delete Playlist"))
                    keyMode = 'TEXT'
                    textBackAction = "PLAYLISTS"
                    textSaveAction = "DELETE_PLAYLIST"
            if self.screen == "1.Q":
                self.footer_text_var.set(str("Press OK to remove Song"))
                keyMode = 'TEXT'
                textBackAction = "QUEUE"
                textSaveAction = "DELETE_SONG"
            return
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
            else:
                self.screen = ''
                self.show_screen()
            return
        if keycode == config["PISCREEN_KEYS"]["right"] or keycode == config["PISCREEN_KEYS"]["ok"]:  # right or return
            if self.listbox.size() > 0:
                selection = int(self.listbox.curselection()[0]) + 1
                new_screen = self.screen + "." + str(selection)
                print(new_screen)
                if new_screen in self.screen_data:
                    if type(self.screen_data[new_screen]) is list:
                        self.screen = new_screen
                        self.show_screen()
                    else:
                        self.run_command(self.screen_data[new_screen]["ACTION"])
                else:
                    if str(new_screen).startswith("1.Q."):
                        menu = new_screen.rsplit(".", maxsplit=1)
                        client.playid(int(queue[int(menu[1])-1]["id"]))
                        return
                    if str(new_screen).startswith("1.P."):
                        menu = new_screen.rsplit(".", maxsplit=1)
                        if menu[1] == "1":
                            keyMode = 'TEXT'
                            textBackAction = 'PLAYLISTS'
                            textSaveAction = 'SAVE_PLAYLIST'
                            textEntry = ''
                            self.footer_text_var.set('Back to Cancel, Ok to Save')
                        else:
                            playlist = playlists[int(menu[1]) - 1]['playlist']
                            client.clear()
                            client.load(playlist)
                            client.play()
                        return
                    if str(new_screen).startswith("1.3.A"):
                        if new_screen.count(".") == 3:
                            menu = new_screen.rsplit(".", maxsplit=1)
                            selectedArtist = artists[int(menu[1])-1]
                            albums = []
                            albums = client.list("album", selectedArtist)
                            albums[:0] = ["Add All"]
                            print("SELECTED Artist "+selectedArtist)
                            self.screen = new_screen
                            self.screen_data[new_screen] = albums
                            self.show_screen()
                            return
                        elif new_screen.count(".") == 4:
                            menu = new_screen.rsplit(".", maxsplit=1)
                            if menu[1] == "1": # add all
                                client.findadd("artist", selectedArtist)
                                print("Added All for artist "+selectedArtist)
                                self.screen = menu[0].rsplit(".", maxsplit=1)[0]
                                self.show_screen()
                            else:
                                selectedAlbum = albums[int(menu[1])-1]
                                songs = client.list("title", "album", selectedAlbum, "artist", selectedArtist)
                                songs[:0] = ["Add All"]
                                self.screen = new_screen
                                self.screen_data[new_screen] = songs
                                self.show_screen()
                                print("Album Selected " + selectedAlbum)
                            return
                        elif new_screen.count(".") == 5:
                            menu = new_screen.rsplit(".", maxsplit=1)
                            if menu[1] == "1":  # add all
                                client.findadd("album", selectedAlbum, "artist", selectedArtist)
                                print("Added All for album/artist " + selectedAlbum + "/" + selectedArtist)
                                self.screen = menu[0].rsplit(".", maxsplit=1)[0]
                                self.show_screen()
                            else:
                                selectedsong = songs[int(menu[1]) - 1]
                                songs = client.findadd("title", selectedsong,"album", selectedAlbum, "artist", selectedArtist)
                                print("Added title/album/artist " + selectedsong + "/" + selectedAlbum + "/" + selectedArtist)
                            return
                    if str(new_screen).startswith("1.3.B"):
                        menu = new_screen.rsplit(".", maxsplit=1)
                        if new_screen.count(".") == 3:
                            selectedAlbum = albums[int(menu[1]) - 1]
                            songs = client.list("title", "album", selectedAlbum)
                            songs[:0] = ["Add All"]
                            self.screen = new_screen
                            self.screen_data[new_screen] = songs
                            self.show_screen()
                            print("Album Selected " + selectedAlbum)
                        if new_screen.count(".") == 4:
                            if menu[1] == "1":  # add all
                                client.findadd("album", selectedAlbum)
                                print("Added All for album " + selectedAlbum)
                                self.screen = menu[0].rsplit(".", maxsplit=1)[0]
                                self.show_screen()
                            else:
                                selectedsong = songs[int(menu[1]) - 1]
                                songs = client.findadd("title", selectedsong,"album", selectedAlbum)
                                print("Added title/album " + selectedsong + "/" + selectedAlbum)
                        return
                    if str(new_screen).startswith("1.3.C"):
                        menu = new_screen.rsplit(".", maxsplit=1)
                        if new_screen.count(".") == 3:
                            selectedGenre = genres[int(menu[1]) - 1]
                            songs = client.list("title", "genre", selectedGenre)
                            self.screen = new_screen
                            self.screen_data[new_screen] = songs
                            self.show_screen()
                            print("Genre Selected " + selectedAlbum)
                        if new_screen.count(".") == 4:
                            selectedsong = songs[int(menu[1]) - 1]
                            songs = client.findadd("title", selectedsong, "genre", selectedGenre)
                            print("Added title/genre " + selectedsong + selectedGenre)
                        return
                print(self.screen)
            return
        if keycode == config["PISCREEN_KEYS"]["vol_up"]:
            if self.volume < 100:
                self.volume += 1
                client.setvol(self.volume)
            return
        if keycode == config["PISCREEN_KEYS"]["vol_down"]:
            self.volume -= 1
            client.setvol(self.volume)
            return
        if keycode == config["PISCREEN_KEYS"]["play"]:
            if status["state"] == "play":
                client.pause()
            else:
                client.play()
            return
        if keycode == config["PISCREEN_KEYS"]["next"]:
            client.next()
            return
        if keycode == config["PISCREEN_KEYS"]["prev"]:
            client.previous()
            return
        if keycode == config["PISCREEN_KEYS"]["home"]:
            self.screen = ''
            self.show_screen()
            return
        print("pressed", repr(event.keycode))

    def run_command(self, action):
        global client, keyMode, textEntry, status
        global albums, artists, queue, songs, playlists, genres
        if action == "QUEUE":
            print("QUEUE")
            local_queue = client.playlistinfo()
            queue.clear()
            for item in local_queue:
                queue.append(item)
            self.screen = "1.Q"
            self.screen_data["1.Q"] = queue
            self.footer_text_var.set("Right to play Song, Menu to delete")
            self.show_screen()
        elif action == "PLAYLISTS":
            print("PLAYLISTS")
            playlists = client.listplaylists()
            playlists[:0] = ["SAVE PLAYLIST"]
            self.screen = "1.P"
            self.screen_data["1.P"] = playlists
            self.footer_text_var.set("Right to play Playlist, Menu to delete")
            self.show_screen()
        elif action == "ARTISTS":
            print("ARTISTS")
            artists = client.list("artist")
            self.screen = "1.3.A"
            self.screen_data["1.3.A"] = artists
            self.show_screen()
        elif action == "ALBUMS":
            print("ALBUMS")
            albums = client.list("album")
            self.screen = "1.3.B"
            self.screen_data["1.3.B"] = albums
            self.show_screen()
        elif action == "GENRES":
            print("GENRES")
            genres = client.list("genre")
            self.screen = "1.3.C"
            self.screen_data["1.3.C"] = genres
            self.show_screen()
        elif action == "UPDATE_LIBRARY":
            print("UPDATE_LIBRARY")
            client.rescan()
        elif action == "SAVE_PLAYLIST":
            keyMode = 'MENU'
            client.save(textEntry)
            textEntry = ''
            self.run_command("PLAYLISTS")
        elif action == "DELETE_PLAYLIST":
            keyMode = 'MENU'
            if textEntry == '1':
                selection = int(self.listbox.curselection()[0])
                client.rm(playlists[selection]['playlist'])
            textEntry = ''
            self.run_command("PLAYLISTS")
        elif action == "DELETE_SONG":
            keyMode = 'MENU'
            client.delete(int(self.listbox.curselection()[0]))
            textEntry = ''
            self.run_command("QUEUE")
        elif action == "CLEAR":
            print("Clearing Queue")
            client.clear()
        elif action == "RANDOM":
            if status['random'] == '0':
                client.random('1')
            else:
                client.random('0')
            status = client.status()
            self.screen_data['1'][5] = "RANDOM "+status['random']
            self.show_screen()
        elif action == "REPEAT":
            if status['repeat'] == '0':
                client.repeat('1')
            else:
                client.repeat('0')
            status = client.status()
            self.screen_data['1'][6] = "REPEAT "+status['repeat']
            self.show_screen()
        elif action == "SINGLE":
            if status['single'] == '0':
                client.single('1')
            else:
                client.single('0')
            status = client.status()
            self.screen_data['1'][7] = "SINGLE "+status['single']
            self.show_screen()
        elif action == "CONSUME":
            if status['consume'] == '0':
                client.consume('1')
            else:
                client.consume('0')
            status = client.status()
            self.screen_data['1'][8] = "CONSUME "+status['consume']
            self.show_screen()
        self.update()
        return

app = PiScreen(root)
app.mainloop()
