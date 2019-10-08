import p3.pad
import random
import math
import p3.state
import p3.read_write as rw

MARTH_RANGE = 30


class Marth:
    def __init__(self):
        self.action_list = []
        self.last_action = 0
        self.previous_state_fields = []
        self.previous_action = None
        self.did_action = False
        self.begin = False
        self.following = False
        self.experiences = 0
        self.trainer = 1
        self.b_count = 0
        self.if_statement_bot = False

    def advance(self, state, pad, sm):
        while self.action_list:
            wait, func, args = self.action_list[0]
            if state.frame - self.last_action < wait:
                return
            else:
                self.action_list.pop(0)
                if func is not None:
                    func(*args)
                self.last_action = state.frame
        else:
            print("my x pos is: " + str(sm.state.players[0].pos_x) + "\n")
            print("my y pos is: " + str(sm.state.players[0].pos_y) + "\n")
            print("i am facing: " + str(sm.state.players[0].facing))
            print("Action State: " + str(sm.state.players[2].action_state))
            self.easy_hunt(pad, sm)
            # if sm.state.players[2].pos_x < -85 or sm.state.players[2].pos_x > 85:
            #     self.recover(pad, sm)
            # else:
            #     self.easy_hunt(pad, sm)
            #     if sm.state.players[2].pos_x < -85 or sm.state.players[2].pos_x > 85:
            #         self.action_list = []

    """ follow until in range, then train """

    def experience(self, state, pad, sm, MEM, DQN, epsilon):
        new_state_fields = sm.field_copy()
        if self.begin:

            print("Experience Total: " + str(self.experiences))
            if (self.experiences >= (100 * self.trainer)):
                self.trainer += 1
                DQN.update_weights(MEM.sample(20))
                rw.write_file(DQN)

            print("Action list length: " + str(len(self.action_list)))

             # while you still have things to do, do them and only them
            while self.action_list:
                print("Thing(s) to do.")
                wait, func, args = self.action_list[0]
                if state.frame - self.last_action < wait:
                    print("Waiting?")
                    return
                else:
                    self.action_list.pop(0)
                    if func is not None:
                        func(*args)
                        print("Executing")
                    self.last_action = state.frame
                    return

            if self.did_action:
                print("Storing")
                # now that you have done stuff (from last time), store the experience
                rew = self.reward(new_state_fields)
                MEM.add((self.previous_state_fields,
                        self.previous_action, rew, new_state_fields))
                self.experiences += 1
                self.did_action = False
            # first see if you can do anything interesting
            if self.in_range(new_state_fields):
                print("In range")
                self.action_list = []
                self.action_list.append(
                    (0, pad.tilt_stick, [p3.pad.Stick.MAIN, 0.5, 0.5]))
                self.following=False
                # if you can do stuff, figure out what to do and add it
                print("Fields: " + str(new_state_fields))
                output_vec=DQN.Q(new_state_fields)
                print("Q out: " + str(output_vec))
                self.previous_state_fields=new_state_fields
                self.previous_action=output_vec
                self.do_action(state, pad, output_vec, epsilon)
                print("New action list length: " + str(len(self.action_list)))
                self.did_action=True
            # if you are not in a position to do anything interesting, add some movement
            else:
                print("Hunting")
                ai_x=sm.state.players[2].pos_x
                pl_x=sm.state.players[0].pos_x
                ai_facing=sm.state.players[0].facing
                if self.following:
                    if (not (pl_x-ai_x > 0 and ai_facing > 0)) or (not (pl_x-ai_x < 0 and ai_facing < 0)):
                        self.easy_hunt(pad, sm)
                else:
                    self.easy_hunt(pad, sm)
                    self.following=True
        else:
            if (0x0142 <= new_state_fields[16] and new_state_fields[16] <= 0x0144):
                self.begin=True

    """The next 3 functions take sf inputs which are lists of state fields following
       the format in StateManager.field_copy()"""

    def reward(self, sf):
        # calculate reward, sf is  current state info (old state info is in marth field)
        dealt=sf[10] - self.previous_state_fields[10]
        taken=sf[24] - self.previous_state_fields[24]
        ai_action_state=sf[16]
        pl_action_state=sf[2]

        # if dead
        if 0x0000 <= ai_action_state and ai_action_state <= 0x000A:
            return -100
        # if shield break
        if 0x00CD <= ai_action_state and ai_action_state <= 0x00D2:
            return -50

        if 0x0000 <= pl_action_state and pl_action_state <= 0x000A:
            return 100

        if 0x00CD <= pl_action_state and pl_action_state <= 0x00D2:
            return 50

        ai_body_state = sf[27]
        if (ai_body_state != 0) and (0x002C <= pl_action_state and pl_action_state <= 0x0045):
            return 20

        diff = (dealt - taken) * 2
        return min(diff, -2) if (diff <= 0) else diff

    def in_range(self, sf):
        # return true if marth ai is in range to attack, sf is current state info
        ai_x=sf[14]
        ai_y=sf[15]
        op_x=sf[0]
        op_y=sf[1]

        delt_x=abs(op_x - ai_x)
        delt_y=abs(op_y - ai_y)
        delt_d=math.sqrt(delt_x**2 + delt_y**2)

        return delt_d <= MARTH_RANGE

    def attack(self, pad, input):
        """ Adds an attack to the action list.

            Parameter input: an array of instruction components
            following the format below:

              input = [0 = direc, 1 = button, 2 = stick, 3 = tilt, 4 = hold, 5 = wait] with
              - direc in [0, 4], 0 = up, 1 = down, 2 = left, 3 = right, 4 = neutral
              - button in [0, 1], 0 = p3.pad.Button.A, 1 = p3.pad.Button.B
              - stick in [0, 1], 0 = p3.pad.Stick.MAIN, 1 = p3.pad.Stick.C
              - tilt in [0, 1], 0 = False, 1 = True
              - hold is an int > 0
              - wait is an int >= 0 """

        if (bool(input[3])):
            d_x=[0.5, 0.5, 0.4, 0.6, 0.5]
            d_y=[0.6, 0.4, 0.5, 0.5, 0.5]
        else:
            d_x=[0.5, 0.5, 0, 1, 0.5]
            d_y=[1, 0, 0.5, 0.5, 0.5]

        btn=[p3.pad.Button.A, p3.pad.Button.B]
        stk=[p3.pad.Stick.MAIN, p3.pad.Stick.C]

        self.action_list.append(
            (0, pad.tilt_stick, [stk[input[2]], d_x[input[0]], d_y[input[0]]]))

        if (not input[2]):
            self.action_list.append((0, pad.press_button, [btn[input[1]]]))
            self.action_list.append(
                (input[4], pad.release_button, [btn[input[1]]]))

        self.action_list.append(
            (0, pad.tilt_stick, [stk[input[2]], 0.5, 0.5]))
        self.action_list.append((input[5], None, []))

    """ Preset attack input combination examples """

    def A_attack(self, pad, direc, hold=1, wait=30):
        self.attack(pad, [direc, 0, 0, 0, hold, wait])

    def B_attack(self, pad, direc, hold=1, wait=30):
        self.attack(pad, [direc, 1, 0, 0, hold, wait])

    def C_attack(self, pad, direc, hold=1, wait=30):
        self.attack(pad, [direc, 0, 1, 0, hold, wait])

    def tilt_attack(self, pad, direc, hold=1, wait=30):
        self.attack(pad, [direc, 0, 0, 1, hold, wait])

    """ direc in [0,3], 0 = up, 1 = down, 2 = left, 3 = right """

    def grab_and_throw(self, pad, direc, wait=30):
        x = [0.5, 0.5, 0, 1]
        y = [1, 0, 0.5, 0.5]
        self.action_list.append((0, pad.press_button, [p3.pad.Button.Z]))
        self.action_list.append(
            (1, pad.release_button, [p3.pad.Button.Z]))
        self.action_list.append(
            (10, pad.tilt_stick, [p3.pad.Stick.MAIN, x[direc], y[direc]]))
        self.action_list.append(
            (10, pad.tilt_stick, [p3.pad.Stick.MAIN, 0.5, 0.5]))
        self.action_list.append((wait, None, []))

    """ marth short hop duration, hold < 3 frames """

    def hop(self, pad, hold, wait=30):
        self.action_list.append((0, pad.press_button, [p3.pad.Button.X]))
        self.action_list.append(
            (hold, pad.release_button, [p3.pad.Button.X]))
        self.action_list.append((wait, None, []))

    """ direc in [0, 2], 0 = down, 1 = left, 2 = right """

    def dodge(self, pad, direc, wait=30):
        x = [0.5, 0, 1]
        y = [0, 0.5, 0.5]
        self.action_list.append((0, pad.press_button, [p3.pad.Button.L]))
        self.action_list.append(
            (0, pad.tilt_stick, [p3.pad.Stick.MAIN, x[direc], y[direc]]))
        self.action_list.append(
            (1, pad.release_button, [p3.pad.Button.L]))
        self.action_list.append(
            (2, pad.tilt_stick, [p3.pad.Stick.MAIN, 0.5, 0.5]))
        self.action_list.append((wait, None, []))

    """ direc in [0, 1], 0 = left, 1 = right """

    def wave_dash(self, pad, direc, wait=30):
        x = [0.1, 0.9]
        y = [0.1, 0.1]
        self.action_list.append((0, pad.press_button, [p3.pad.Button.X]))
        self.action_list.append(
            (1, pad.release_button, [p3.pad.Button.X]))
        self.action_list.append(
            (1, pad.tilt_stick, [p3.pad.Stick.MAIN, x[direc], y[direc]]))
        self.action_list.append((3, pad.press_button, [p3.pad.Button.L]))
        self.action_list.append(
            (5, pad.release_button, [p3.pad.Button.L]))
        self.action_list.append(
            (7, pad.tilt_stick, [p3.pad.Stick.MAIN, 0.5, 0.5]))
        self.action_list.append((wait, None, []))

    def shield(self, pad, hold=1, wait=30):
        self.action_list.append((0, pad.press_button, [p3.pad.Button.L]))
        self.action_list.append(
            (hold, pad.release_button, [p3.pad.Button.L]))
        self.action_list.append((wait, None, []))

    def wb_smash(self, pad, sm, wait=30):
        facing =sm.state.players[2].facing
        if facing>0:
            wd = 0
        else:
            wd = 1
        self.wave_dash(pad, wd, 0)
        self.A_attack(pad, wd, 3)

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

    def easy_hunt(self, pad, sm):
        pl = sm.state.players[0]
        ai = sm.state.players[2]
        delt_x = abs(pl.pos_x - ai.pos_x)
        delt_y = abs(pl.pos_y - ai.pos_y)
        delt_d = math.sqrt(delt_x**2 + delt_y**2)

        actions = [lambda _ : self.shffair(pad, sm),
        lambda _ : self.shfair(pad, sm),
        lambda _ : self.shn(pad),
        lambda _ : self.wb_smash(pad, sm, 10)
        ]

        if ai.pos_x < 85 and ai.pos_x > -85:
            self.b_count = 0

        #stay on stage
        if ai.pos_x > 85:
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, 0, .5]))

        # stay on stage
        if ai.pos_x < -85:
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, 1, .5]))

        #recover side B
        if ai.pos_y < -10 and ai.pos_x > 120 and self.b_count <10:
            self.b_count += 1
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, 0, .5]))
            self.action_list.append((0, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append((1, pad.release_button, [p3.pad.Button.B]))
            self.action_list.append((0, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append((1, pad.release_button, [p3.pad.Button.B]))
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, .35, .75]))
            self.action_list.append((1, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append(
                    (1, pad.release_button, [p3.pad.Button.B]))

        #recover side B
        if ai.pos_y < -10 and ai.pos_x < -120 and self.b_count <10:
            self.b_count += 1
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, 1, .5]))
            self.action_list.append((0, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append((1, pad.release_button, [p3.pad.Button.B]))
            self.action_list.append((0, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append((1, pad.release_button, [p3.pad.Button.B]))
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, .85, .75]))
            self.action_list.append((1, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append(
                    (1, pad.release_button, [p3.pad.Button.B]))

        #recover up B
        if ai.pos_y < -40 and ai.pos_x > 80:
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, .35, .75]))
            self.action_list.append((0, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append(
                    (1, pad.release_button, [p3.pad.Button.B]))

        #recover up B
        if ai.pos_y < -40 and ai.pos_x < -80:
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, .85, .75]))
            self.action_list.append((0, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append(
                    (1, pad.release_button, [p3.pad.Button.B]))

        # down smash if in range
        if (delt_d <= MARTH_RANGE) and self.if_statement_bot:
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, 0.5, 0.5]))
            # self.wb_smash(pad, 3)
            # self.action_list = []
            if ((0x002C <= pl.action_state.value and pl.action_state.value <= 0x004A) or
            (0x0155 <= pl.action_state.value and pl.action_state.value <= 0x0158)):
                self.shield(pad, 2)
                return

            index = random.randint(0, len(actions)-1)
            actions[index](0)
            return

        # follow opponent until edge
        if pl.pos_x > ai.pos_x and ai.pos_x < 89.2:
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, 1, 0.5]))

        # follow opponent until edge
        elif pl.pos_x <= ai.pos_x and ai.pos_x > -89.2:
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, 0, 0.5]))
        # else:
        #     self.action_list.append(
        #          (0, pad.tilt_stick, [p3.pad.Stick.MAIN, 0.5, 0]))

        # jump if below opponent
        if pl.pos_y > ai.pos_y:
            self.action_list.append((0, pad.press_button, [p3.pad.Button.X]))
            self.action_list.append(
                    (1, pad.release_button, [p3.pad.Button.X]))

        # wait
        self.action_list.append((10, None, []))

    def recover(self, pad, sm):
        pl = sm.state.players[0]
        ai = sm.state.players[2]
        delt_x = abs(pl.pos_x - ai.pos_x)
        delt_y = abs(pl.pos_y - ai.pos_y)
        delt_d = math.sqrt(delt_x**2 + delt_y**2)
        if ai.pos_x < 85 and ai.pos_x > -85:
            self.b_count = 0

        #stay on stage
        if ai.pos_x > 85:
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, 0, .5]))

        # stay on stage
        if ai.pos_x < -85:
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, 1, .5]))

        #recover side B
        if ai.pos_y < -10 and ai.pos_x > 120 and self.b_count <10:
            self.b_count += 1
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, 0, .5]))
            self.action_list.append((0, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append((1, pad.release_button, [p3.pad.Button.B]))
            self.action_list.append((0, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append((1, pad.release_button, [p3.pad.Button.B]))
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, .35, .75]))
            self.action_list.append((1, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append(
                    (1, pad.release_button, [p3.pad.Button.B]))

        #recover side B
        if ai.pos_y < -10 and ai.pos_x < -120 and self.b_count <10:
            self.b_count += 1
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, 1, .5]))
            self.action_list.append((0, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append((1, pad.release_button, [p3.pad.Button.B]))
            self.action_list.append((0, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append((1, pad.release_button, [p3.pad.Button.B]))
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, .85, .75]))
            self.action_list.append((1, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append(
                    (1, pad.release_button, [p3.pad.Button.B]))

        #recover up B
        if ai.pos_y < -40 and ai.pos_x > 80:
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, .35, .75]))
            self.action_list.append((0, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append(
                    (1, pad.release_button, [p3.pad.Button.B]))

        #recover up B
        if ai.pos_y < -40 and ai.pos_x < -80:
            self.action_list.append(
                (0, pad.tilt_stick, [p3.pad.Stick.MAIN, .85, .75]))
            self.action_list.append((0, pad.press_button, [p3.pad.Button.B]))
            self.action_list.append(
                    (1, pad.release_button, [p3.pad.Button.B]))

    def do_action(self, state, pad, output, epsilon):
        """
        does action from vector of possible actions once within range of enemy
        at index of argmax of output
        """
        print("Doing")
        actions_vector = [lambda _ : self.attack(pad, [4,0,0,0,1,1]), #    0 - neutral basic attack
                      lambda _ : self.attack(pad, [2,0,0,1,1,1]), #    1 - left smash
                      lambda _ : self.attack(pad, [3,0,0,1,1,1]), #    2 - right smash
                      lambda _ : self.attack(pad, [0,0,0,1,1,1]), #    3 - up smash
                      lambda _ : self.attack(pad, [1,0,0,1,1,1]), #    4 - down smash
                      lambda _ : self.attack(pad, [4,1,0,0,1,1]), # 5 - neutral b
                      lambda _ : self.attack(pad, [2,1,0,1,1,1]), # 6 - left b
                      lambda _ : self.attack(pad, [3,1,0,1,1,1]), #7 - right b
                      lambda _ : self.attack(pad, [0,1,0,1,1,1]), #8 - up b
                      lambda _ : self.attack(pad, [1,1,0,1,1,1]), # 9 - down b
                      lambda _ : self.dodge(pad, 1, 1), #10 - left dodge
                      lambda _ : self.dodge(pad, 2, 1), #11 - right dodge
                      lambda _ : self.dodge(pad, 0, 1), #12 - down dodge
                      lambda _ : self.wave_dash(pad, 0, 1), #13 - left wave dash
                      lambda _ : self.wave_dash(pad, 1, 1), #14 - right wave dash
                      lambda _ : self.shield(pad, 10, 1), # 15 - shield
                      lambda _ : self.hop(pad, 1, 1), #16 - short hop
                      lambda _ : self.hop(pad, 4, 1), # 17 - long hop
                      lambda _ : self.grab_and_throw(pad, 2, 1), #18 - grab and throw left
                      lambda _ : self.grab_and_throw(pad, 3, 1), #19 - grab and throw right
                      lambda _ : self.grab_and_throw(pad, 0, 1), #20 - grab and throw up
                      lambda _ : self.grab_and_throw(pad, 1, 1), #21 - grab and throw down
                      ]
        mx = output[0]
        index = 0
        for i in range(len(output)-1):
            if output[1+i] > mx:
                mx = output[1+i]
                index = 1+i

        if epsilon > random.uniform(0, 1):
            index = random.randint(0, 21)
        actions_vector[index](0)

"""
            if self.map_analysis == -100:
                self.map_analysis = sm.state.players[0].pos_x
                print("Starting position: " + str(self.map_analysis))
            if abs(sm.state.players[0].pos_x - self.map_analysis) > 5:
                self.map_analysis = sm.state.players[0].pos_x
                print("New position is: " + str(self.map_analysis))

            print("my x pos is: " + str(sm.state.players[0].pos_x) + "\n")
            print("my y pos is: " + str(sm.state.players[0].pos_y) + "\n")
            print("i am facing: " + str(sm.state.players[0].facing))
            print("Action State: " + str(sm.state.players[2].action_state))

            # print("Action State P1: " + str(sm.state.players[0].action_state))
            # print("Action State AI: " + str(sm.state.players[2].action_state))
            # Eventually this will point at some decision-making thing.
            # self.A_attack(pad, 0.5, 1, p3.pad.Stick.MAIN, 30)   # up A
            # self.B_attack(pad, 0.5, 1, p3.pad.Stick.MAIN)       # up B
            # self.C_attack(pad, 0.5, 1)                          # up C
            # self.tilt_attack(pad, 0)                            # up tilt
            # self.hop(pad, 2)                                    # short hop
            # self.hop(pad, 4)                                    # long hop
            # self.dodge(pad, 2)                                  # down dodge
            # self.dodge(pad, 0)                                  # left dodge
            # self.dodge(pad, 1)                                  # right dodge
            # left wave dash
            # self.wave_dash(pad, 0)
            # right wave dash
            # self.wave_dash(pad, 1)
            # self.wave_dash(pad, 0)

            if 0x002C <= sm.state.players[0].action_state.value and sm.state.players[0].action_state.value <=0x0045:
                self.dodge(pad, 0)
            elif (sm.state.players[2].pos_x - sm.state.players[0].pos_x < 30 or
            sm.state.players[2].pos_x - sm.state.players[0].pos_x < -30):
                self.attack(pad, [1,0,0,0,3,30])
            else:
                self.wave_dash(pad, 1)                              # right wave dash
                self.wave_dash(pad, 0)

            # self.random_move(pad)
            # self.easy_hunt(pad, sm)

                def random_move(self, pad):
        move_list = [p3.pad.Button.A, p3.pad.Button.B, p3.pad.Button.X,
                     p3.pad.Button.Y, p3.pad.Button.Z, p3.pad.Button.L,
                     p3.pad.Button.R, p3.pad.Button.D_UP,
                     p3.pad.Button.D_DOWN, p3.pad.Button.D_LEFT,
                     p3.pad.Button.D_RIGHT]
        random.shuffle(move_list)
        move = move_list[0]
        self.action_list.append((0, pad.press_button, [move]))
        self.action_list.append((1, pad.release_button, [move]))
        self.action_list.append((1, None, []))

        # def train(self, state, pad, sm):
    #     while self.action_list:
    #         wait, func, args = self.action_list[0]
    #         if state.frame - self.last_action < wait:
    #             return
    #         else:
    #             self.action_list.pop(0)
    #             if func is not None:
    #                 func(*args)
    #             self.last_action = state.frame
    #     else:
    #         return
"""
