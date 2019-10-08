import os.path
import time

import p3.marth
import p3.memory_watcher
import p3.menu_manager
import p3.pad
import p3.state
import p3.state_manager
import p3.stats
import p3.read_write as rw

from p3.Network import Memory
from p3.Network import DQNetwork

EPSILON = 1


def find_dolphin_dir():
    """Attempts to find the dolphin user directory. None on failure."""
    candidates = ['~/.dolphin-emu', '~/.local/share/.dolphin-emu',
                  '~/Library/Application Support/Dolphin']
    for candidate in candidates:
        path = os.path.expanduser(candidate)
        if os.path.isdir(path):
            return path
    return None


def write_locations(dolphin_dir, locations):
    """Writes out the locations list to the appropriate place under dolphin_dir."""
    path = dolphin_dir + '/MemoryWatcher/Locations.txt'
    with open(path, 'w') as f:
        f.write('\n'.join(locations))

        dolphin_dir = find_dolphin_dir()
        if dolphin_dir is None:
            print('Could not detect dolphin directory.')
            return


def run(marth, state, sm, mw, pad, stats, MEM, DQN):
    epsilon = EPSILON
    mm = p3.menu_manager.MenuManager()
    while True:
        last_frame = state.frame
        res = next(mw)
        if res is not None:
            sm.handle(*res)
        if state.frame > last_frame:
            stats.add_frames(state.frame - last_frame)
            start = time.time()
            make_action(state, pad, mm, marth, sm, MEM, DQN, epsilon)
            epsilon = max((epsilon - 0.0001), 0)
            #print("\nEpsilon: " + str(epsilon) + "\n")
            stats.add_thinking_time(time.time() - start)


def make_action(state, pad, mm, marth, sm, MEM, DQN, epsilon):
    if state.menu == p3.state.Menu.Game:
        #marth.experience(state, pad, sm, MEM, DQN, epsilon)
        marth.if_statement_bot = True
        marth.advance(state, pad, sm)
    elif state.menu == p3.state.Menu.Characters:
        mm.char_setup(state, pad)
    elif state.menu == p3.state.Menu.Stages:
        mm.final_dest(state, pad)
    elif state.menu == p3.state.Menu.PostGame:
        mm.train(state, pad, MEM, DQN)


def main():
    dolphin_dir = find_dolphin_dir()
    if dolphin_dir is None:
        print('Could not find dolphin config dir.')
        return

    state = p3.state.State()
    sm = p3.state_manager.StateManager(state)
    write_locations(dolphin_dir, sm.locations())

    stats = p3.stats.Stats()

    marth = p3.marth.Marth()

    try:
        print('Start dolphin now. Press ^C to stop p3.')
        pad_path = dolphin_dir + '/Pipes/p3'
        mw_path = dolphin_dir + '/MemoryWatcher/MemoryWatcher'
        with p3.pad.Pad(pad_path) as pad, p3.memory_watcher.MemoryWatcher(mw_path) as mw:
            network = rw.read_file()
            run(marth, state, sm, mw, pad, stats, Memory(50), network)
    except KeyboardInterrupt:
        print('Stopped')
        print(stats)


if __name__ == '__main__':
    main()
