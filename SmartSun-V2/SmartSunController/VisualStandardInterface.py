from SmartSunController.Assets.Display import display_controller
from SmartSunController.Assets.Buzzer import buzzer_controller
from SmartSunController.Assets.LightController import LightController

import time
import threading
from functools import partial

class VSI():
    def __init__(self, buzz_pin: int = None, led_pin: int = None, ip: str = None, debug: bool = False):
        self.buzz = buzzer_controller(buzz_pin) if buzz_pin != None else None
        self.led = LightController(led_pin) if led_pin != None else None
        self.disp = display_controller()
        self.ip = ip

        self.thread = None
        self.stop_event = threading.Event()
        self._debug = debug

        self.mem_cline_1 = None
        self.mem_cline_2 = None

    @property
    def _classname(self):
        return self.__class__.__name__

    def __del__(self):
        #self.disp.lcd_send_command('CS'), this implementation doesn't work (which makes absolutely sense). And also, the display doesnt support it.
        print(f'[{self._classname}] finished.')

    def mem_print(self, msg, cline: int = None, center: bool = True):
        self.mem_cline_1 = [msg, center] if cline == 1 else self.mem_cline_1
        self.mem_cline_2 = [msg, center] if cline == 2 else self.mem_cline_2
        if cline:
            if self.mem_cline_1 != None:
                self.disp.cdprint(self.mem_cline_1[0], cline=1, center=self.mem_cline_1[1])
            if self.mem_cline_2 != None:
                self.disp.cdprint(self.mem_cline_2[0], cline=2, center=self.mem_cline_2[1])
        else:
            self.disp.dprint(msg)


    def clear_cline_mem(self):
        self.mem_cline_1 = None
        self.mem_cline_2 = None


    def auto_print(self, msg, cline: int):
        if len(msg) >= 16:
            splitted_msg = list(msg)
            for i in range(len(splitted_msg) - 15):
                if self.stop_event.is_set():
                    break
                msg = ''.join(splitted_msg[i:i+16])
                self.disp.cdprint(msg=msg, cline=cline, center=False)
                if i == 0: time.sleep(1)
                time.sleep(.5)
        else:
            self.mem_print(msg, cline=2)

    def startup(self):
        self.led.turn_off()
        self.mem_print('THE SMARTSUN', cline=1, center=True)
        for i in range(17):
            self.mem_print(('#' * i), cline=2, center=False)
            self.buzz.single_beep()
        return
    
    def standard(self):
        self.led.turn_off()
        self.mem_print('THE SMARTSUN', cline=1)
        ipstr = f"The webinterface can be found at: {self.ip}"
        while not self.stop_event.is_set():
            self.auto_print(ipstr, cline=2)
        return
    
    def error(self):
        if not self.stop_event.is_set():
            self.mem_print('ERROR', cline=1)
            self.buzz.error_beep()
            self.led.turn_on()
        return


    def _ThreadedJob(self, job: str = 'standard'):
        while not self.stop_event.is_set():
            if job == 'startup':
                self.startup()
            elif job == 'standard':
                self.standard()
            elif job == 'error':
                self.error()
            if self.stop_event.is_set():
                    if self._debug: print(f"[{self._classname}] Thread exitting.")
                    return
        
    def startThreadedJob(self, job):
        if self.thread and self.thread.is_alive():
            return
        
        target_function = partial(self._ThreadedJob, job=job)
        self.thread = threading.Thread(target=target_function)
        self.thread.start()
        return

    def stopThreadedJob(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join()
            time.sleep(2)
            self.stop_event.clear()
            if self._debug: print(f'[{self._classname}] Thread exitted succesfully.')



        
    
