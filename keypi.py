#!/bin/python 
from __future__ import print_function
import RPi.GPIO as GPIO
from time import sleep
import datetime,sys

import curses
import curses.textpad

class NcursePrinter(object):
   def __init__(self):
     self.dihdah_buff=""
     self.text_buff=""
     curses.wrapper(self)
   
   def __call__(self,scr):
     self.scr = scr
     self.start()

   def start(self):
     self.scr.border(0)
     

     self.begin_x = 1
     self.begin_y = 1
     self.height = 3
     self.width = 70
     self.dihdah_win = curses.newwin(self.height, self.width, self.begin_y, self.begin_x)
     self.dihdah_win.box()
     self.text_win = curses.newwin(self.height, self.width, self.begin_y+self.height, self.begin_x)
     self.text_win.box()
     # self.dihdah_tb = curses.textpad.Textbox(self.dihdah_win)
     # dihdah_text =  dihdah_tb.edit()
     # self.scr.refresh()

   def add_dihdah(self,text):
     self.dihdah_buff += text
     dmin = max(0,len(self.dihdah_buff)-self.width+2)
     self.dihdah_buff = self.dihdah_buff[dmin:] # take last chars
     self.dihdah_win.addstr(1,1,self.dihdah_buff)
     self.dihdah_win.refresh()

   def add_text(self,text):
     self.text_buff += text
     dmin = max(0,len(self.text_buff)-self.width+2)
     self.text_buff = self.text_buff[dmin:] # take last chars
     self.text_win.addstr(1,1,self.text_buff)
     self.text_win.refresh()

   def close(self):
     curses.endwin()

class MorseKey(object):
  def __init__(self):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(22, GPIO.IN)

  def read_state(self):
    return GPIO.input(22)

class Morse(object):

  morsetab = {
         '.-'    : 'A', '-----' : '0',        
         '-...'  : 'B', '.----' : '1',          
         '-.-.'  : 'C', '..---' : '2',          
         '-..'   : 'D', '...--' : '3',          
         '.'     : 'E', '....-' : '4',          
         '..-.'  : 'F', '.....' : '5',          
         '--.'   : 'G', '-....' : '6',          
         '....'  : 'H', '--...' : '7',          
         '..'    : 'I', '---..' : '8',          
         '.---'  : 'J', '----.' : '9',          
         '-.-'   : 'K', '--..--': ',',          
         '.-..'  : 'L', '.-.-.-': '.',          
         '--'    : 'M', '..--..': '?',          
         '-.'    : 'N', '-.-.-.': ';',          
         '---'   : 'O', '---...': ':',          
         '.--.'  : 'P', '.----.': "'",          
         '--.-'  : 'Q', '-....-': '-',          
         '.-.'   : 'R', '-..-.' : '/',          
         '...'   : 'S', '-.--.-': '(',          
         '-'     : 'T', '-.--.-': ')',          
         '..-'   : 'U', '..--.-': '_',          
         '...-'  : 'V',          
         '.--'   : 'W',          
         '-..-'  : 'X',          
         '-.--'  : 'Y',          
         '--..'  : 'Z',}

  keymorse = {v:k for k, v in morsetab.items()}

  def __init__(self,pooling=0.05,speed=20,key=None,printer=None):

    self.key = key
    self.printer = printer
    # speed is in words per minute
    # PARIS is the reference word composed of 50 elements 
    self.speed = speed
    self.pooling = pooling 
    self.delta_zero = datetime.timedelta(0)

    self.delta_element = datetime.timedelta(microseconds=(1000000 *  60/(50 * self.speed)))

    self.delta_dit =   self.delta_element
    self.delta_dah = 3*self.delta_element    
    self.delta_inter_character = 3*self.delta_element
    self.delta_inter_word = 7*self.delta_element

    self.delta_dit_max = self.delta_dit + self.delta_dit
    self.delta_dah_max = self.delta_dah + self.delta_dit


    self.UP = 0
    self.DOWN = 1
    self.buff =""

    self.lastchar=" " 

  # def mp(self,data):
  #   #print(data, end="")
  #   self.lastchar = data
  #   sys.stdout.flush()

  def reset_buff(self):
    self.buff = ""

  def prefix(self):
    for morse in self.morsetab.keys():
      if morse.startswith(self.buff):
        return True
    return False

  def try_decode(self):
    l = self.morsetab.get(self.buff)
    if not l:
      l = "#"
    self.lastchar = l
    self.printer.add_text(l)
    

  def check_possible(self):
    if (not self.prefix()):
      self.reset_buff()
      l = "#"
      self.lastchar = l
      self.printer.add_text(l)

  def loop(self):
   
     
    state = GPIO.input(22)
    t = datetime.datetime.today()

    # print("Start listening at {} wpm.\n"
    #       "Element period is {} ms".format(self.speed, self.delta_dit.microseconds/1000))

    while True:
      new_state = self.key.read_state()
      nt = datetime.datetime.today()
      d = (nt - t)
      if (new_state != state):       
        t = nt
        state = new_state
        if new_state == self.UP: # previous state was down
          if self.delta_zero < d < self.delta_dit_max:
            # self.mp(".")
            self.printer.add_dihdah(".")
            self.buff += "."
            self.check_possible()
          elif self.delta_dit_max < d <self.delta_dah_max:
            # self.mp("-")
            self.printer.add_dihdah("-")
            self.buff += "-"
            self.check_possible()
          else:
            # self.mp("*")
            self.printer.add_dihdah("*")
            self.reset_buff()
      elif new_state == self.UP:
          if self.delta_inter_character < d and len(self.buff) !=0:
            self.try_decode()
            self.reset_buff()
          elif self.delta_inter_word < d and self.lastchar != " ":
            self.lastchar = " "
            self.printer.add_text(" ")
            t = nt

     
      sleep(self.pooling)  

k = MorseKey()
p = NcursePrinter()
m = Morse(speed=13,key=k,printer=p)


m.loop()
