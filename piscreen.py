#!/usr/bin/env python3
import tkinter, mpd, configparser, subprocess, sys
from tkinter import Listbox, Label, Canvas, Frame, Y, X
from PIL import Image, ImageTk, ImageColor
from subprocess import call
from pathlib import Path

root = tkinter.Tk()
root.geometry("320x240")
client = mpd.MPDClient(use_unicode=True)
config = configparser.ConfigParser()
config.read('config.ini')

theme_name=config["THEME"]["theme"]
theme = configparser.ConfigParser()
theme.read('./theme/'+theme_name+'/theme.ini')

icon_random = None
icon_repeat = None
icon_single = None

status = {}

queue = []
playlists = []
artists = []
albums = []
genres = []
songs = []
themes = []

selectedAlbum = ''
selectedArtist = ''
selectedGenre = ''
currentSong = None

keyMode = 'MENU'
textEntry = ''
textBackAction = ''
textSaveAction = ''

image = None
bg = None
awayCount = 0
footerMessage = ''
footerMessageCount = 0
minTickerLength = 30
songName = ''
songChanged = False
songTicker = False
songTickerCount = 0
volumeChanged = False

class PiScreen(tkinter.Frame):

    def __init__(self, master: 'tkinter.Tk'):
        global client, status, theme
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
            "1.4": ["UPDATE LIBRARY", "THEMES"],
            "1.4.1": {"ACTION": "UPDATE_LIBRARY"},
            "1.4.2": {"ACTION": "THEMES"},
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
        self.playerScreen = Canvas(self, width=320, height=240, bg=theme['PLAYER']['background'], borderwidth=0, highlightthickness=0)

        self.menuScreen = Frame(self, width=320, height=240, bg="white")
        self.menuScreen.place(height=240, width=320, x=0, y=0)

        # Menu Screen items
        self.headerFrame = Frame(self.menuScreen, width=320, height=20, bg=theme['HEADER']['background'])
        self.headerFrame.pack(side=tkinter.TOP, fill=X)

        self.currentSongLabel = Label(self.headerFrame, font=(theme['HEADER']['font'], 12, 'bold'), bg=theme['HEADER']['background'], foreground=theme['HEADER']['foreground'], textvariable=self.current_song_var, justify=tkinter.LEFT, anchor=tkinter.W)
        self.currentSongLabel.place(x=0, y=0, width=300, height=20, anchor=tkinter.NW)

        self.volumeLabel = Label(self.headerFrame, font=(theme['HEADER']['font'], 10, 'bold'), bg=theme['HEADER']['background'], foreground=theme['HEADER']['foreground'], text='')
        self.volumeLabel.place(x=300, y=0, anchor=tkinter.NW)

        self.mainFrame = Frame(self.menuScreen, width=320, height=200)
        self.mainFrame.pack(side=tkinter.TOP, fill=Y)

        self.listbox = Listbox(self.mainFrame, selectmode=tkinter.SINGLE, font=(theme['MAIN']['font'], 11), bg=theme['MAIN']['background'],
                               fg=theme['MAIN']['foreground'], height=10, activestyle="none", borderwidth=0, highlightthickness=0, selectbackground=theme['MAIN']['selected'], selectforeground=theme['MAIN']['foreground'])
        self.listbox.bind("<Key>", self.handle_keys)
        self.listbox.configure(width=320, height=11)
        self.listbox.pack(side=tkinter.TOP, expand=1, ipadx=0, ipady=0, padx=0, pady=0)
        self.listbox.focus_set()

        self.footer = Label(self.menuScreen, textvariable=self.footer_text_var, font=(theme['FOOTER']['font'], 10, 'bold'), bg=theme['FOOTER']['background'],
                            foreground=theme['FOOTER']['foreground'], justify=tkinter.LEFT, anchor=tkinter.W)
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
                        self.listbox.insert(tkinter.END, item[:38])
                if format == "SONG":
                    songname = ''
                    if 'artist' in item:
                        songname = item['artist'][:18]
                    songname += " - "
                    if 'title' in item:
                        max = 38 - len(songname)
                        songname += item['title'][:max]
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
        global image, bg, songChanged, volumeChanged
        if songChanged or image is None:
            if sys.platform.startswith('linux'):
                process = subprocess.Popen("./coverart.sh", shell=True, stdout=subprocess.PIPE).stdout.read()
            else:
                process = "./icons/ic_album_white_48dp.png"
            image = ImageTk.PhotoImage(Image.open(process).resize((136,136), Image.ANTIALIAS))
        if bg is None:
            process = "./icons/bg.png"
            if 'img_background' in theme['PLAYER']:
                process = theme['PLAYER']['img_background']
            bg = ImageTk.PhotoImage(Image.open(process).resize((320, 240), Image.ANTIALIAS))
        if icon_random is None:
            self.load_icons()

        if status["state"] == "play":
            if songChanged:
                self.playerScreen.create_image(160, 120, image=bg)

                self.playerScreen.create_rectangle(10, 10, 150, 150, fill=theme['PLAYER']['foreground'])
                self.playerScreen.create_image(80, 80, image=image)

                self.playerScreen.create_image(178, 132, image=icon_random)
                self.playerScreen.create_image(224, 132, image=icon_repeat)
                self.playerScreen.create_image(270, 132, image=icon_single)
                self.playerScreen.create_rectangle(298, 146, 308, 92, fill=theme['PLAYER']['background'], outline=theme['PLAYER']['foreground'], width=1)
                self.playerScreen.create_line(303, 144, 303, 144 - int(self.volume / 2), fill=theme['PLAYER']['foreground'], width=7)

                self.playerScreen.create_text(10, 160, text=currentSong['artist'], anchor=tkinter.NW, fill=theme['PLAYER']['foreground'],
                                              font=(theme['PLAYER']['font'], 14, 'bold'))
                self.playerScreen.create_text(10, 185, text=currentSong['title'], anchor=tkinter.NW, fill=theme['PLAYER']['foreground'],
                                              font=(theme['PLAYER']['font'], 12, 'bold'))
                self.playerScreen.create_text(10, 210, text=currentSong['album'], anchor=tkinter.NW, fill=theme['PLAYER']['foreground'],
                                              font=(theme['PLAYER']['font'], 10, 'bold'))
            else:
                time = str(status['time']).split(":")
                played = int((float(time[0])/float(time[1]))*320)
                if played < 3: # bug
                    self.playerScreen.create_rectangle(0, 236, 320, 240, fill=theme['PLAYER']['background'])
                self.playerScreen.create_rectangle(0, 236, played, 240, fill=theme['PLAYER']['foreground'])
            if volumeChanged:
                volumeChanged = False
                self.playerScreen.create_rectangle(298, 146, 308, 92, fill=theme['PLAYER']['background'],
                                               outline=theme['PLAYER']['foreground'], width=1)
                self.playerScreen.create_line(303, 144, 303, 144 - int(self.volume / 2), fill=theme['PLAYER']['foreground'],
                                          width=7)
        else:   # Blank Screen
            self.playerScreen.create_image(160, 120, image=bg)
            self.playerScreen.create_text(20, 20, text=theme['PLAYER']['default_message'], anchor=tkinter.NW, fill=theme['PLAYER']['foreground'],
                                          font=(theme['PLAYER']['font'], 20, 'bold'))
        songChanged = False
        return

    def handle_keys(self, event):
        global config, client, selectedAlbum, selectedArtist, selectedGenre
        global keyMode, textEntry, textBackAction, textSaveAction, awayCount, theme_name
        global albums, artists, queue, songs, playlists, status, genres, songChanged, volumeChanged

        awayCount = 0
        keycode = str(event.keycode)
        # self.footer_text_var.set(str("Key Pressed : "+keycode))
        if keyMode == 'PLAYER' and keycode != config["PISCREEN_KEYS"]["vol_up"] \
                and keycode != config["PISCREEN_KEYS"]["vol_down"]  \
                and keycode != config["PISCREEN_KEYS"]["play"]  \
                and keycode != config["PISCREEN_KEYS"]["next"]  \
                and keycode != config["PISCREEN_KEYS"]["prev"]  \
                and keycode != config["PISCREEN_KEYS"]["power"] \
                and keycode != config["PISCREEN_KEYS"]["left"]:
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
                songChanged = True
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
                    if str(new_screen).startswith("1.4.T"):
                        menu = new_screen.rsplit(".", maxsplit=1)
                        theme_name = themes[int(menu[1]) - 1]
                        self.footer_text_var.set("Applying Theme " + theme_name)
                        self.apply_theme()
            return
        if keycode == config["PISCREEN_KEYS"]["vol_up"]:
            if self.volume < 100:
                self.volume += 1
                client.setvol(self.volume)
                volumeChanged = True
                self.footer_text_var.set("Volume Up")
            else:
                self.footer_text_var.set("Volume Max!!")
            return
        if keycode == config["PISCREEN_KEYS"]["vol_down"]:
            if self.volume > 0:
                self.volume -= 1
                client.setvol(self.volume)
                volumeChanged = True
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
        global albums, artists, queue, songs, playlists, genres, themes
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
        elif action == "THEMES":
            self.footer_text_var.set("Select Theme")
            themes = ["default", "foofighters", "light"]
            self.screen = "1.4.T"
            self.screen_data["1.4.T"] = themes
            self.show_screen()
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
            self.update_random()
            self.show_screen()
        elif action == "REPEAT":
            if status['repeat'] == '0':
                client.repeat('1')
            else:
                client.repeat('0')
            status = client.status()
            self.screen_data['1'][6] = "REPEAT "+status['repeat']
            self.update_repeat()
            self.show_screen()
        elif action == "SINGLE":
            if status['single'] == '0':
                client.single('1')
            else:
                client.single('0')
            status = client.status()
            self.screen_data['1'][7] = "SINGLE "+status['single']
            self.update_single()
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

    def load_icons(self):
        self.update_random()
        self.update_repeat()
        self.update_single()

    def update_random(self):
        global status, theme, icon_random
        fgcolor = ImageColor.getrgb(theme['PLAYER']['foreground'])
        bgcolor = ImageColor.getrgb(theme['PLAYER']['background'])
        fgcolor += (255,)
        bgcolor += (255,)
        icon_random = Image.open('./icons/ic_shuffle_white_36dp.png')
        if icon_random.mode != 'RGBA':
            icon_random = icon_random.convert('RGBA')
        data = list(icon_random.getdata())
        newData = list()
        for pixel in data:
            if pixel[3] != 0:
                if status['random'] == '1':
                    newData.append(fgcolor)
                else:
                    newData.append(bgcolor)
            else:
                newData.append(pixel)
        icon_random.putdata(newData)
        icon_random = ImageTk.PhotoImage(icon_random.resize((36, 36), Image.ANTIALIAS))

    def update_single(self):
        global status, theme, icon_single
        fgcolor = ImageColor.getrgb(theme['PLAYER']['foreground'])
        bgcolor = ImageColor.getrgb(theme['PLAYER']['background'])
        fgcolor += (255,)
        bgcolor += (255,)
        icon_single = Image.open('./icons/ic_repeat_one_white_36dp.png')
        if icon_single.mode != 'RGBA':
            icon_single = icon_single.convert('RGBA')
        data = list(icon_single.getdata())
        newData = list()
        for pixel in data:
            if pixel[3] != 0:
                if status['single'] == '1':
                    newData.append(fgcolor)
                else:
                    newData.append(bgcolor)
            else:
                newData.append(pixel)
        icon_single.putdata(newData)
        icon_single = ImageTk.PhotoImage(icon_single.resize((36, 36), Image.ANTIALIAS))

    def update_repeat(self):
        global status, theme, icon_repeat
        fgcolor = ImageColor.getrgb(theme['PLAYER']['foreground'])
        bgcolor = ImageColor.getrgb(theme['PLAYER']['background'])
        fgcolor += (255,)
        bgcolor += (255,)
        icon_repeat = Image.open('./icons/ic_repeat_white_36dp.png')
        if icon_repeat.mode != 'RGBA':
            icon_repeat = icon_repeat.convert('RGBA')
        data = list(icon_repeat.getdata())
        newData = list()
        for pixel in data:
            if pixel[3] != 0:
                if status['repeat'] == '1':
                    newData.append(fgcolor)
                else:
                    newData.append(bgcolor)
            else:
                newData.append(pixel)
        icon_repeat.putdata(newData)
        icon_repeat = ImageTk.PhotoImage(icon_repeat.resize((36, 36), Image.ANTIALIAS))

    def apply_theme(self):
        global theme_name, theme, config, bg
        my_file = Path('./theme/' + theme_name + '/theme.ini')
        if my_file.is_file():
            theme = configparser.ConfigParser()
            theme.read('./theme/' + theme_name + '/theme.ini')
            # player related settings
            bg = None
            self.playerScreen.configure(bg=theme['PLAYER']['background'])
            self.load_icons()
            # menu related settings
            self.headerFrame.configure(bg=theme['HEADER']['background'])
            self.currentSongLabel.configure(font=(theme['HEADER']['font'], 12, 'bold'),
                                            bg=theme['HEADER']['background'], foreground=theme['HEADER']['foreground'])
            self.volumeLabel.configure(font=(theme['HEADER']['font'], 10, 'bold'), bg=theme['HEADER']['background'],
                                       foreground=theme['HEADER']['foreground'])
            self.listbox.configure(font=(theme['MAIN']['font'], 11), bg=theme['MAIN']['background'],
                                   fg=theme['MAIN']['foreground'], selectbackground=theme['MAIN']['selected'], selectforeground=theme['MAIN']['foreground'])
            self.footer.configure(font=(theme['FOOTER']['font'], 10, 'bold'), bg=theme['FOOTER']['background'],
                                  foreground=theme['FOOTER']['foreground'])

            # write theme to config.ini
            config["THEME"]["theme"] = theme_name
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
        else:
            self.footer_text_var.set("Theme Not Found")
            theme_name = config["THEME"]["theme"]

app = PiScreen(root)
app.mainloop()
