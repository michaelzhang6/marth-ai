import p3.pad
import random
import math
import p3.state
import p3.read_write as rw
import p3.marth as m

class Attacks(m.Marth):
    def __init__(self):
        m.Marth.__init__(self)


    #short hop double fair
    def shffair(self, pad, sm):
        facing =sm.state.players[2].facing
        if (facing == 1): 
            direc = 1
        else:
            direc = 0

        #short hop
        self.action_list.append((0, pad.press_button, [p3.pad.Button.X]))
        self.action_list.append(
            (2, pad.release_button, [p3.pad.Button.X]))
      
        #first fair - first frame after becoming airborne - test this
        self.action_list.append((2, pad.tilt_stick, [p3.pad.Stick.MAIN, direc, .5]))
        self.action_list.append((0, pad.press_button, [p3.pad.Button.A]))
        self.action_list.append((1, pad.release_button, [p3.pad.Button.A]))

        #second fair- frame 29?
        self.action_list.append((24, pad.press_button, [p3.pad.Button.A]))
        self.action_list.append((1, pad.release_button, [p3.pad.Button.A]))

        #Lcancel- last 7 frames of landing
        self.action_list.append((2, pad.press_button, [p3.pad.Button.R]))
        self.action_list.append((1, pad.release_button, [p3.pad.Button.R]))

        #reset sticks
        self.action_list.append((2, pad.tilt_stick, [p3.pad.Stick.MAIN, .5, .5]))
        self.action_list.append((36, None, []))

    #short hop single fair
    def shfair(self, pad, sm):
        facing =sm.state.players[2].facing
        if (facing == 1): 
            direc = 1
        else:
            direc = 0

        #short hop
        self.action_list.append((0, pad.press_button, [p3.pad.Button.X]))
        self.action_list.append((2, pad.release_button, [p3.pad.Button.X]))

        #fair
        self.action_list.append((3, pad.tilt_stick, [p3.pad.Stick.MAIN, direc, .5]))
        self.action_list.append((0, pad.press_button, [p3.pad.Button.A]))
        self.action_list.append((1, pad.release_button, [p3.pad.Button.A]))

        #fast fall
        self.action_list.append((6, pad.tilt_stick, [p3.pad.Stick.MAIN, .5, 0]))

        #Lcancel- last 7 frames of landing
        self.action_list.append((17, pad.press_button, [p3.pad.Button.R]))
        self.action_list.append((1, pad.release_button, [p3.pad.Button.R]))
         
        #reset sticks
        self.action_list.append((2, pad.tilt_stick, [p3.pad.Stick.MAIN, .5, .5]))
        self.action_list.append((36, None, []))

    #short hop nair
    def shn(self, pad):
        #short hop
        self.action_list.append((0, pad.press_button, [p3.pad.Button.X]))
        self.action_list.append((2, pad.release_button, [p3.pad.Button.X]))
        
        #nair
        self.action_list.append((3, pad.press_button, [p3.pad.Button.A]))
        self.action_list.append((1, pad.release_button, [p3.pad.Button.A]))

        #fast fall
        self.action_list.append((6, pad.tilt_stick, [p3.pad.Stick.MAIN, .5, 0]))

        #Lcancel- last 7 frames of landing
        self.action_list.append((18, pad.press_button, [p3.pad.Button.R]))
        self.action_list.append((1, pad.release_button, [p3.pad.Button.R]))

        #reset sticks
        self.action_list.append((2, pad.tilt_stick, [p3.pad.Stick.MAIN, .5, .5]))
        self.action_list.append((36, None, []))

    #wavedash-back forward smash
    def wb_smash(self, pad, sm):
        facing =sm.state.players[2].facing
        if (facing == 1): 
            direc = 0
        else:
            direc = 1

        self.wave_dash(pad, direc, 0)
        self.A_attack(pad, facing, 3)

    