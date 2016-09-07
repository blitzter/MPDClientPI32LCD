#!/usr/bin/env python3
import configparser, tkinter
from tkinter import Label

config = configparser.ConfigParser()
config.read('config.ini')
config_found = False
if len(config.sections()) > 0 and config.has_section("PISCREEN_KEYS"):
    print("Config Found!!")
    config_found = True
else:
    print("Config Not Found!!")
    config_found = False

root = tkinter.Tk()
root.geometry("320x240")

class ConfigLoader(tkinter.Frame):

    def __init__(self, master: 'tkinter.Tk'):
        tkinter.Frame.__init__(self, master, padx=0, pady=0)
        self.pack()
        self.place(height=240, width=320, x=0, y=0)
        self.config(bg="black")

        self.headerText = 'Config Loader'
        self.headerTextVar = tkinter.StringVar()
        self.headerTextVar.set(str(self.headerText))

        self.headerLabel = Label(self, font=('lucidatypewriter', 10, 'bold'), bg='grey', foreground='white', textvariable=self.headerTextVar)
        self.headerLabel.configure(width=320, height=1)
        self.headerLabel.pack(side = tkinter.TOP)

        self.list_keys = ["OK","UP","DOWN","LEFT","RIGHT","BACK","HOME","VOL_UP","VOL_DOWN","MUTE","MENU","PLAY","NEXT","PREV"]
        self.list_values = {}
        self.counter = 0
        self.key_name = "OK"
        self.key_tries = 0
        self.key_values = []
        self.keylabel_text = 'Press key for OK :'
        self.keylabel_text_var = tkinter.StringVar()
        self.keylabel_text_var.set(str(self.keylabel_text))
        self.keylabel = Label(self, textvariable=self.keylabel_text_var, font=('lucidatypewriter', 10, 'bold'), bg='grey',
                            foreground='black')
        self.keylabel.configure(width=320, height=1)
        self.keylabel.pack(side = tkinter.TOP)

        self.footer_text_var = tkinter.StringVar()
        self.footer_text_var.set(str("Press key for OK :"))
        self.footer = Label(self, textvariable=self.footer_text_var, font=('lucidatypewriter', 10, 'bold'), bg='grey',
                            foreground='black')
        self.footer.configure(width=320, height=1)
        self.footer.pack(side = tkinter.BOTTOM)

        self.focus_set()
        self.bind("<Key>", self.key)

    def key(self, event):
        # self.keylabel_text_var.set(str("Some Data Entered!!"))
        self.key_tries += 1
        if self.key_tries == 3:
            if self.key_values[0] == event.keycode and self.key_values[1] == event.keycode:
                print("saving key "+self.key_name)
                self.footer_text_var.set(str("Setting Value "+self.key_name+"-"+str(event.keycode)))
                self.list_values[self.key_name] = event.keycode
                self.counter += 1
                if self.counter == len(self.list_keys):
                    self.write_settings()
                else:
                    self.key_name = self.list_keys[self.counter]
                    self.key_values = []
                    self.key_tries = 0
                    self.keylabel_text_var.set("Press key for " + self.key_name + " :")
            else:
                self.key_tries = 0
                self.key_values = []
                self.footer_text_var.set(str("Try again!! Mismatch"))
        else:
            self.key_values.append(event.keycode)
            self.keylabel_text_var.set("Press key for "+self.key_name+" :"+str(event.keycode))

    def write_settings(self):
        global root
        if config_found == False:
            config.add_section("PISCREEN_KEYS")
        for ITEM in self.list_keys:
            config["PISCREEN_KEYS"][ITEM] = str(self.list_values[ITEM])
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        root.quit()

app = ConfigLoader(root)
app.mainloop()


# config['DEFAULT'] = {'ServerAliveInterval': '45',
#                      'Compression': 'yes',
#                      'CompressionLevel': '9'}
# config['bitbucket.org'] = {}
# config['bitbucket.org']['User'] = 'hg'
# config['topsecret.server.com'] = {}
# topsecret = config['topsecret.server.com']
# topsecret['Port'] = '50022'     # mutates the parser
# topsecret['ForwardX11'] = 'no'  # same here
# config['DEFAULT']['ForwardX11'] = 'yes'
# with open('example.ini', 'w') as configfile:
#   config.write(configfile)
