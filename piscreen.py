#!/usr/bin/env python3
import tkinter, mpd, configparser, subprocess, sys
from tkinter import Listbox, Label, Canvas, Frame, Y, X
from PIL import Image, ImageTk
from subprocess import call

root = tkinter.Tk()
root.geometry("320x240")
client = mpd.MPDClient(use_unicode=True)
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
awayCount = 0
footerMessage = ''
footerMessageCount = 0
minTickerLength = 30
songName = ''
songChanged = False
songTicker = False
songTickerCount = 0

class PiScreen(tkinter.Frame):

    def __init__(self, master: 'tkinter.Tk'):
        global client, status
        #host = '192.168.1.120'
        host = 'localhost'
        if sys.platform.startswith('linux'):
            host = 'localhost'
        client.connect(host, 6600)
        tkinter.Frame.__init__(self, master, padx=0, pady=0)
        self.pack()
        self.place(height=240, width=320, x=0, y=0)
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

        self.current_song_var = tkinter.StringVar()
        self.footer_text_var = tkinter.StringVar()

        # Screens
        self.playerScreen = Canvas(self, width=320, height=240, bg="black", borderwidth=0, highlightthickness=0)

        self.menuScreen = Frame(self, width=320, height=240, bg="white")
        self.menuScreen.place(height=240, width=320, x=0, y=0)

        # Menu Screen items
        self.headerFrame = Frame(self.menuScreen, width=320, height=20, bg="black")
        self.headerFrame.pack(side=tkinter.TOP, fill=X)

        self.currentSongLabel = Label(self.headerFrame, font=('courier', 12, 'bold'), bg='black', foreground='white', textvariable=self.current_song_var, justify=tkinter.LEFT, anchor=tkinter.W)
        self.currentSongLabel.place(x=0, y=0, width=300, height=20, anchor=tkinter.NW)

        self.volumeLabel = Label(self.headerFrame, font=('lucidatypewriter', 10, 'bold'), bg='black', foreground='white', text='')
        self.volumeLabel.place(x=300, y=0, anchor=tkinter.NW)

        self.mainFrame = Frame(self.menuScreen, width=320, height=200)
        self.mainFrame.pack(side=tkinter.TOP, fill=Y)

        self.listbox = Listbox(self.mainFrame, selectmode=tkinter.SINGLE, font=('lucidatypewriter', 11), bg='black',
                               fg='white', height=10, activestyle="none", borderwidth=0, highlightthickness=0)
        self.listbox.bind("<Key>", self.handle_keys)
        self.listbox.configure(width=320, height=11)
        self.listbox.pack(side=tkinter.TOP, expand=1, ipadx=0, ipady=0, padx=0, pady=0)
        self.listbox.focus_set()

        self.footer = Label(self.menuScreen, textvariable=self.footer_text_var, font=('lucidatypewriter', 10, 'bold'), bg='black',
                            foreground='white', justify=tkinter.LEFT, anchor=tkinter.W)
        self.footer.configure(width=320, height=1)
        self.footer.pack(side = tkinter.BOTTOM)

        self.focus_set()
        self.bind("<Key>", self.handle_keys)
        self.screen = "1"
        self.show_screen()
        self.tick()

    def tick(self):
        global awayCount, keyMode, footerMessage, footerMessageCount
        self.update_header()
        if keyMode != 'PLAYER':
            awayCount += 1
            if awayCount > 120:
                awayCount = 0
                self.screen = ''
                self.show_screen()
        else:
            awayCount = 0

        if footerMessage == self.footer_text_var.get():
            footerMessageCount += 1
            if footerMessageCount > 8:
                footerMessageCount = 0
                self.footer_text_var.set("")
        else:
            footerMessage = self.footer_text_var.get()
            footerMessageCount = 0

        self.after(800, self.tick)

    def update_header(self):
        global status, keyMode, songChanged, currentSong, songName, songTicker, minTickerLength, songTickerCount
        status = client.status()
        self.volume = int(status["volume"])
        header = ''
        self.volumeLabel.configure(text=status["volume"])
        if status["state"] == "play":
            currentSong = client.currentsong()
            song = currentSong["artist"] + " - " + currentSong["title"]
            if songName != song:
                songChanged = True
                if keyMode != 'PLAYER': # song changed, refresh ui
                    songName = song
                    if len(songName) >= minTickerLength:
                        songTicker = True
                        songTickerCount = -1
                    else:
                        songTicker = False
                        songTickerCount = 0
            if keyMode != 'PLAYER':
                if songTicker:
                    songTickerCount += 1
                    if songTickerCount == len(songName) + 5:
                        songTickerCount = 0
                song = songName + "     "
                new_song = song[songTickerCount:] + song[:songTickerCount]
                self.current_song_var.set(new_song)
            elif keyMode == 'PLAYER':
                self.show_player()
        else:
            if songName != '':
                self.current_song_var.set('')
                songName = ''
                songChanged = True
                if keyMode == 'PLAYER':
                    self.show_player()

    def show_screen(self):
        global keyMode
        if self.screen == '':
            keyMode = 'PLAYER'
            self.menuScreen.place_forget()
            self.playerScreen.place(height=240, width=320, x=0, y=0)
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
                        self.listbox.insert(tkinter.END, "")
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
        global image, status, currentSong, songChanged
        if songChanged or image is None:
            if sys.platform.startswith('linux'):
                process = subprocess.Popen("./coverart.sh", shell=True, stdout=subprocess.PIPE).stdout.read()
            else:
                process = "./icons/bg.png"
            image = ImageTk.PhotoImage(Image.open(process).resize((320,240), Image.ANTIALIAS))

        if status["state"] == "play":
            if songChanged:
                self.playerScreen.create_image(160, 120, image=image)
                #self.playerScreen.create_rectangle(151, 1, 320, 150, fill="black")

                self.playerScreen.create_text(15, 130, text=currentSong['artist'], anchor=tkinter.NW, fill="white",
                                              font=('lucidatypewriter', 14, 'bold'))
                self.playerScreen.create_text(15, 155, text=currentSong['title'], anchor=tkinter.NW, fill="white",
                                              font=('lucidatypewriter', 12, 'bold'))
                self.playerScreen.create_text(15, 180, text=currentSong['album'], anchor=tkinter.NW, fill="white",
                                              font=('lucidatypewriter', 10, 'bold'))
        else:
            self.playerScreen.create_image(160, 120, image=image)
            #self.playerScreen.create_rectangle(151, 1, 320, 150, fill="black")
            self.playerScreen.create_text(20, 20, text="Play Something!!", anchor=tkinter.NW, fill="white",
                                          font=('lucidatypewriter', 20, 'bold'))
        songChanged = False
        return

    def handle_keys(self, event):
        global config, client, selectedAlbum, selectedArtist, selectedGenre
        global keyMode, textEntry, textBackAction, textSaveAction, awayCount
        global albums, artists, queue, songs, playlists, status, genres

        awayCount = 0
        keycode = str(event.keycode)
        # self.footer_text_var.set(str("Key Pressed : "+keycode))
        if keyMode == 'PLAYER' and keycode != config["PISCREEN_KEYS"]["vol_up"] \
                and keycode != config["PISCREEN_KEYS"]["vol_down"]  \
                and keycode != config["PISCREEN_KEYS"]["play"]  \
                and keycode != config["PISCREEN_KEYS"]["next"]  \
                and keycode != config["PISCREEN_KEYS"]["prev"]  \
                and keycode != config["PISCREEN_KEYS"]["power"]:
            keyMode = 'MENU'
            self.playerScreen.place_forget()
            self.menuScreen.place(height=240, width=320, x=0, y=0)
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
                            self.footer_text_var.set("SELECTED Artist "+selectedArtist)
                            self.screen = new_screen
                            self.screen_data[new_screen] = albums
                            self.show_screen()
                            return
                        elif new_screen.count(".") == 4:
                            menu = new_screen.rsplit(".", maxsplit=1)
                            if menu[1] == "1": # add all
                                client.findadd("artist", selectedArtist)
                                self.footer_text_var.set("Added All for "+selectedArtist)
                                self.screen = menu[0].rsplit(".", maxsplit=1)[0]
                                self.show_screen()
                            else:
                                selectedAlbum = albums[int(menu[1])-1]
                                songs = client.list("title", "album", selectedAlbum, "artist", selectedArtist)
                                songs[:0] = ["Add All"]
                                self.screen = new_screen
                                self.screen_data[new_screen] = songs
                                self.show_screen()
                                self.footer_text_var.set("Album Selected " + selectedAlbum)
                            return
                        elif new_screen.count(".") == 5:
                            menu = new_screen.rsplit(".", maxsplit=1)
                            if menu[1] == "1":  # add all
                                client.findadd("album", selectedAlbum, "artist", selectedArtist)
                                self.footer_text_var.set("Added All for " + selectedAlbum + "/" + selectedArtist)
                                self.screen = menu[0].rsplit(".", maxsplit=1)[0]
                                self.show_screen()
                            else:
                                selected_song = songs[int(menu[1]) - 1]
                                client.findadd("title", selected_song,"album", selectedAlbum, "artist", selectedArtist)
                                self.footer_text_var.set("Added " + selected_song + "/" + selectedAlbum + "/" + selectedArtist)
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
                            self.footer_text_var.set("Album Selected " + selectedAlbum)
                        if new_screen.count(".") == 4:
                            if menu[1] == "1":  # add all
                                client.findadd("album", selectedAlbum)
                                self.footer_text_var.set("Added All for album " + selectedAlbum)
                                self.screen = menu[0].rsplit(".", maxsplit=1)[0]
                                self.show_screen()
                            else:
                                selected_song = songs[int(menu[1]) - 1]
                                client.findadd("title", selected_song,"album", selectedAlbum)
                                self.footer_text_var.set("Added " + selected_song + "/" + selectedAlbum)
                        return
                    if str(new_screen).startswith("1.3.C"):
                        menu = new_screen.rsplit(".", maxsplit=1)
                        if new_screen.count(".") == 3:
                            selectedGenre = genres[int(menu[1]) - 1]
                            songs = client.list("title", "genre", selectedGenre)
                            self.screen = new_screen
                            self.screen_data[new_screen] = songs
                            self.show_screen()
                            self.footer_text_var.set("Genre Selected " + selectedAlbum)
                        if new_screen.count(".") == 4:
                            selected_song = songs[int(menu[1]) - 1]
                            client.findadd("title", selected_song, "genre", selectedGenre)
                            self.footer_text_var.set("Added " + selected_song + selectedGenre)
                        return
            return
        if keycode == config["PISCREEN_KEYS"]["vol_up"]:
            if self.volume < 100:
                self.volume += 1
                client.setvol(self.volume)
                self.footer_text_var.set("Volume Up")
            else:
                self.footer_text_var.set("Volume Max!!")
            return
        if keycode == config["PISCREEN_KEYS"]["vol_down"]:
            if self.volume > 0:
                self.volume -= 1
                client.setvol(self.volume)
                self.footer_text_var.set("Volume Down")
            else:
                self.footer_text_var.set("Volume Zero!!")
            return
        if keycode == config["PISCREEN_KEYS"]["play"]:
            if status["state"] == "play":
                client.pause()
                self.footer_text_var.set("Paused")
            else:
                client.play()
                self.footer_text_var.set("Playing")
            return
        if keycode == config["PISCREEN_KEYS"]["next"]:
            client.next()
            self.footer_text_var.set("Next Song")
            return
        if keycode == config["PISCREEN_KEYS"]["prev"]:
            client.previous()
            self.footer_text_var.set("Previous Song")
            return
        if keycode == config["PISCREEN_KEYS"]["home"]:
            self.screen = ''
            self.show_screen()
            return
        if keycode == config["PISCREEN_KEYS"]["power"]:
            if sys.platform.startswith('linux'):
                call("sudo nohup shutdown -h now", shell=True)
            else:
                self.footer_text_var.set("Can't PowerOff from remote")
            return
        self.footer_text_var.set("UNKNOWN "+keycode)

    def run_command(self, action):
        global client, keyMode, textEntry, status
        global albums, artists, queue, songs, playlists, genres
        if action == "QUEUE":
            local_queue = client.playlistinfo()
            queue.clear()
            for item in local_queue:
                queue.append(item)
            self.screen = "1.Q"
            self.screen_data["1.Q"] = queue
            self.footer_text_var.set("Right to play Song, Menu to delete")
            self.show_screen()
        elif action == "PLAYLISTS":
            playlists = client.listplaylists()
            playlists[:0] = ["SAVE PLAYLIST"]
            self.screen = "1.P"
            self.screen_data["1.P"] = playlists
            self.footer_text_var.set("Right to play Playlist, Menu to delete")
            self.show_screen()
        elif action == "ARTISTS":
            artists = client.list("artist")
            self.screen = "1.3.A"
            self.screen_data["1.3.A"] = artists
            self.show_screen()
        elif action == "ALBUMS":
            albums = client.list("album")
            self.screen = "1.3.B"
            self.screen_data["1.3.B"] = albums
            self.show_screen()
        elif action == "GENRES":
            genres = client.list("genre")
            self.screen = "1.3.C"
            self.screen_data["1.3.C"] = genres
            self.show_screen()
        elif action == "UPDATE_LIBRARY":
            self.footer_text_var.set("Updating library")
            client.update()
        elif action == "SAVE_PLAYLIST":
            keyMode = 'MENU'
            found = False
            if textEntry == '':
                self.footer_text_var.set("Name Empty!!")
                return
            for playlist in playlists:
                if isinstance(playlist, str) is False and textEntry == playlist['playlist']:
                    found = True
            if found:
                client.rm(textEntry)
                client.save(textEntry)
            else:
                client.save(textEntry)
            self.footer_text_var.set("Saved Playlist "+textEntry)
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
            self.footer_text_var.set("Clearing Queue")
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
