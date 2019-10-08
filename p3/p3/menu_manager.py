import math

import p3.pad


class MenuManager:
    def __init__(self):
        self.in_place = False
        self.cpu_setter = 0
        self.marth_picked = False
        self.cpu_selected = False
        self.diff_set = False
        self.start = False

    """
        self.selected_marth = False

    def pick_marth(self, state, pad):
        if self.selected_marth:
            # Release buttons
            pad.release_button(p3.pad.Button.A)
            pad.tilt_stick(p3.pad.Stick.MAIN, 0.5, 0.5)
        else:
            # Go to marth and press A
            target_x = 12
            target_y = 4
            dx = target_x - state.players[2].cursor_x
            dy = target_y - state.players[2].cursor_y
            mag = math.sqrt(dx * dx + dy * dy)
            if mag < 0.3:
                pad.press_button(p3.pad.Button.A)
                self.selected_marth = True
            else:
                pad.tilt_stick(p3.pad.Stick.MAIN, 0.5 *
                               (dx / mag) + 0.5, 0.5 * (dy / mag) + 0.5)
    """

    """ AI picks Marth and sets a level 9 CPU to play against """

    def char_setup(self, state, pad):
        if not self.marth_picked:
            self.pick_marth(state, pad)
        else:
            if not self.cpu_selected:
                self.select_cpu(state, pad)
            else:
                if not self.diff_set:
                    self.set_diff(state, pad)
                else:
                    # for some reason, won't press final START
                    # ALSO, dk where cursor is in memory for stage select
                    pad.tilt_stick(p3.pad.Stick.MAIN, 0.5, 0.5)
                    if self.start:
                        pad.release_button(p3.pad.Button.START)
                    else:
                        pad.press_button(p3.pad.Button.START)
                        self.start = True

    def move_to(self, state, pad, x, y, eps=0.3):
        if not self.in_place:
            dx = x - state.players[2].cursor_x
            dy = y - state.players[2].cursor_y
            ad = math.sqrt(dx * dx + dy * dy)
            if ad < eps:
                pad.tilt_stick(p3.pad.Stick.MAIN, 0.5, 0.5)
                self.in_place = True
            else:
                pad.tilt_stick(p3.pad.Stick.MAIN, 0.5 *
                               (dx / ad) + 0.5, 0.5 * (dy / ad) + 0.5)

    def pick_marth(self, state, pad):
        if self.cpu_setter == 1:
            pad.release_button(p3.pad.Button.A)
            self.cpu_setter += 1
            self.marth_picked = True
        else:
            self.move_to(state, pad, 11, 4)
            if self.in_place:
                pad.press_button(p3.pad.Button.A)
                self.cpu_setter += 1
                self.in_place = False

    def select_cpu(self, state, pad):
        if self.cpu_setter == 6:
            pad.release_button(p3.pad.Button.A)
            self.cpu_setter += 1
            self.cpu_selected = True
        elif self.cpu_setter == 5:
            pad.press_button(p3.pad.Button.A)
            self.cpu_setter += 1
        elif self.cpu_setter == 4:
            pad.release_button(p3.pad.Button.A)
            self.cpu_setter += 1
        elif self.cpu_setter == 3:
            pad.press_button(p3.pad.Button.A)
            self.cpu_setter += 1
        elif self.cpu_setter == 2:
            self.move_to(state, pad, -30, -2, 0.4)
            if self.in_place:
                self.cpu_setter += 1
                self.in_place = False

    def set_diff(self, state, pad):
        if self.cpu_setter == 9:
            pad.release_button(p3.pad.Button.A)
            self.cpu_setter += 1
            self.diff_set = True
        elif self.cpu_setter == 8:
            pad.release_button(p3.pad.Button.A)
            self.move_to(state, pad, -21, -15)
            if self.in_place:
                pad.press_button(p3.pad.Button.A)
                self.cpu_setter += 1
                self.in_place = False
        elif self.cpu_setter == 7:
            self.move_to(state, pad, -30, -15, 0.6)
            if self.in_place:
                pad.press_button(p3.pad.Button.A)
                self.cpu_setter += 1
                self.in_place = False

    def final_dest(self, state, pad):
        return

    def train(self, state, pad, MEM, DQN):
        if self.cpu_setter == 10:
            pad.release_button(p3.pad.Button.START)
            self.cpu_setter += 1
        elif self.cpu_setter == 9:
            DQN.update_weights(MEM.sample(50))
            pad.press_button(p3.pad.Button.START)
            self.cpu_setter += 1
