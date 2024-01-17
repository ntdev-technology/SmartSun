import configparser
import os
import ast
import time
import threading
from functools import partial

from SmartSunController.SmartSunCore.Misc import NTPtime, EthernetInfo
from SmartSunController.SmartSunCore.SmartSunPos import SmartSunPos
from SmartSunController.exceptions import *
from SmartSunController.SmartSunCore.SmartSun_GPIO_Controller import stepper_controller
from SmartSunController.SmartSunCore.Misc import GPIO_utils
from SmartSunController.VisualStandardInterface import VSI

class Controller():
    def __init__(self):
        self._SETTINGS_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'setup.ini')
        self._MEMORY_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'memory.ini')
        self._STATUS = 'Ok'
        self.MALFUNCTION = None

        self.integrety_check()

        self.stepperInstances = []
        self.settings_in_userset = None
        self.TimeCtr = None
        self.Steppers = []
        self.Calc_cnf = None
        self.Calc_val = None
        self.Loc_set = None
        self.Rel_cords = None
        self.timezone = None
        self.debug = None

        self.Man_time = None
        self.Stepper_save = None
        self.Current_angle = None
        self.last_time_checked = None

        self.Buzzer_pin = None
        self.Led_pin = None

        self._set_settings()

        self.adjust_perpendicular_angle_azim = True
        self.adjust_perpendicular_angle_elev = True

        self.preferred_hold_time = 30 # Time step/deg func holds.
        self.preferred_long_hold_time = 30 * 60

        try:
            try:
                self.VSI = VSI(self.Buzzer_pin, self.Led_pin, self._ip, debug=self.debug)
            except Exception:
                raise MajorSystemMalfunction("Malfunction 55 - Uncorrected error")
        except MajorSystemMalfunction as e:
            self.MALFUNCTION = e

        self.ntptime = NTPtime()

        self.thread = None
        self._VSI_thread_running = False
        self._stop_event = threading.Event()

        self.GUtils = GPIO_utils()

        self._RegisterSteppers()
        self.VSIStart()


    def __del__(self):
        print(f"[{self._classname}] finished.")
    
    @property
    def _classname(self) -> str:
        return self.__class__.__name__

    @property
    def _settings(self) -> list:
        config = configparser.ConfigParser()
        config.read(self._SETTINGS_PATH)

        if ('Settings' in config) and ('UserSet' in config):
            return [config.sections(), dict(config['Settings']), dict(config['UserSet'])]
        else:
            raise IntegrityCheckFailed("Module failed to load due to corrupted or non-existend ini file.")
    
    @property
    def _ip(self) -> str:
        ether = EthernetInfo()
        return str(ether.MyIP())


    def integrety_check(self) -> None:
        check = True
        self._status = 'Failing'
        checklst_set = ["settings_in_userset", "timectr", "steppers", "stepper_cnf", "calc_cnf", "calc_val", "loc_set", "rel_cords", "buzzer_pin", "led_pin"]
        checklst_usr = ["timezone", "debug"]
        settings_present = list(self._settings[1])
        usr_present = list(self._settings[2])

        check = True if 'Settings' in self._settings[0] and 'UserSet' in self._settings[0] else False
        try:
            for i in range(len(checklst_set)):
                check = True if settings_present[i] in checklst_set and len(checklst_set) == len(settings_present) else False
            for q in range(len(checklst_usr)):
                check = True if usr_present[q] in checklst_usr and len(checklst_usr) == len(usr_present) else False 
        except:
            check = False

        if check:
            self._status = 'Ok'

        else: raise FileError("Malfunction 32 - IntegretyCheckFailed // Not all settings present in 'setup.ini?' ")
        
    def VSIStart(self) -> None:
        if self.debug: print(f'[{self._classname}] Visual startup...')
        if self._VSI_thread_running: self.VSI.stopThreadedJob(); self._VSI_thread_running = False
        self.VSI.startThreadedJob(job='startup'); self._VSI_thread_running = True
        self.VSI.stopThreadedJob(); self._VSI_thread_running = False
        return

    def VSINormal(self) -> None:
        if self._VSI_thread_running: self.VSI.stopThreadedJob(); self._VSI_thread_running = False
        self.VSI.startThreadedJob(job='standard'); self._VSI_thread_running = True
        return

    def VSIError(self) -> None:
        if self._VSI_thread_running: self.VSI.stopThreadedJob(); self._VSI_thread_running = False
        self.VSI.startThreadedJob('error'); self._VSI_thread_running = True
        self.VSI.stopThreadedJob(); self._VSI_thread_running = False
        return

    def _set_settings(self, res_thread: bool = False) -> None: # set to True to load a selection
        try:
            try:
                settings_dict = self._settings[1]
                self.TimeCtr = settings_dict['timectr']
                            
                if not res_thread: 
                    stepper_define = ast.literal_eval(settings_dict['stepper_cnf'])
                    for stepper in range(len(stepper_define)):
                        curr_list = ast.literal_eval(settings_dict['steppers'])
                        self.Steppers.append([stepper_define[stepper], curr_list[stepper]])

                self.Calc_cnf = settings_dict['calc_cnf']
                self.Calc_val = int(settings_dict['calc_val'])
                self.Loc_set = settings_dict['loc_set']
                if not res_thread: self.Rel_cords = ast.literal_eval(settings_dict['rel_cords'])
                if not res_thread: self.Buzzer_pin = int(settings_dict['buzzer_pin'])
                if not res_thread: self.Led_pin = int(settings_dict['led_pin'])
                if not res_thread: self.settings_in_userset = ast.literal_eval(settings_dict['settings_in_userset'])

            except Exception:
                raise FileError("Malfunction 30 - FileError // in setup.ini")

            try: 
                userset_dict = self._settings[2]
                self.timezone = int(userset_dict['timezone'])
                debug = str(userset_dict['debug'])
                self.debug = True if debug in ['yes', 'True', 'true'] else False

            except Exception:
                raise FileError("Malfunction 30 - FileError // in setup.ini")
        except FileError as e:
            self.MALFUNCTION = e

        
    def _RegisterSteppers(self) -> None:
        if self.debug: print(f"[{self._classname}] Registering steppers...")
        for i in range(int(len(self.Steppers))):
            self.stepperInstances.append(stepper_controller(pins=tuple(self.Steppers[i][1]), which=(self.Steppers[i][0]), debug=(self.debug)))

    def _memory(self, store: bool = False, load: bool = True, overwrite: bool = False) -> list | None:
        config = configparser.ConfigParser()
        config.read(self._MEMORY_PATH)
        if store:
            if self.debug: print(f"[{self._classname}] Writing memory...")
            config.set('Memory', 'manual_time', str(self.Man_time))
            config.set('Memory', 'stepper_save', str(self.Stepper_save)) # exa: [stepper1, stepper2]
            config.set('Memory', 'current_angle', str(self.Current_angle))
            config.set('Memory', 'last_time_checked', str(self.last_time_checked))
            with open(self._MEMORY_PATH, 'w') as configfile:
                config.write(configfile)
            return
        
        elif load:
            if self.debug: print(f"[{self._classname}] Reading memory...")
            man_time = ast.literal_eval(config.get('Memory', 'manual_time'))
            stepper_save = ast.literal_eval(config.get('Memory', 'stepper_save'))
            current_angle = ast.literal_eval(config.get('Memory', 'current_angle'))
            last_time_checked = ast.literal_eval(config.get('Memory', 'last_time_checked'))
            if not overwrite:
                return [man_time, stepper_save, current_angle, last_time_checked]
            else:
                if self.debug: print(f"[{self._classname}] Overwriting local variables from memory...")
                self.Man_time = man_time
                self.Stepper_save = stepper_save
                self.Current_angle = current_angle
                self.last_time_checked = last_time_checked
        
        else:
            return
        
    def setManTime(self, man_time) -> None:
        man_time_list = list(man_time)
        man_time_list.append(self.timezone)
        self.Man_time = tuple(man_time_list)
        self._memory(store=True)
        return

        
    def ChangeSetting(self, **kwargs) -> None:
        if self.debug: print(f"[{self._classname}] Changing setting...")
        if not kwargs:
            raise UserError('Malfunction 23 - Arguments not profided.')
        
        keys = [key for key, new_value in kwargs.items()]

        if self.debug: print(f"[{self._classname}] Changing: {keys}")
        try:
            for i in range(len(keys)):
                section = 'Settings' if keys[i] not in self.settings_in_userset else 'UserSet'

                config = configparser.ConfigParser()
                config.read(self._SETTINGS_PATH)

                try:
                    config.set(section, keys[i], str(kwargs.get(keys[i])))
                    
                    with open(self._SETTINGS_PATH, 'w') as configfile:
                        config.write(configfile)
                    
                except:
                    raise MajorSystemMalfunction('Malfunction 54 - Major system failure.')
        except MajorSystemMalfunction as e:
            self.MALFUNCTION = e
            pass

    
    def _CalultatePosition(self) -> list:
        _man_time = [] # Just declare it, otherwise it will throw a malfunction in the 'system' mode.
        system_time = False

        if self.debug: print(f"[{self._classname}] Calculating current position...")
        if self.debug: print(f"[{self._classname}] Time controller: {self.TimeCtr}")
        for i in range(len(self.Rel_cords)):
            if self.Loc_set == self.Rel_cords[i][0]:
                if self.Loc_set == 'Nl':
                    #self.timezone = 2
                    pass
                elif self.Loc_set == 'UK':
                    # FIX: maybe timezone correction.
                    pass
                else:
                    raise UserError('Malfunction 20')
                self._memory(store=True)
                self.ChangeSetting(timezone=self.timezone)
                location = tuple(self.Rel_cords[i][1])
                if self.debug: print(f"[{self._classname}] location: {location}")
        
        match self.TimeCtr:
            case 'manual':
                man_time = self._memory()[0]
                _adjust_timezone = False if self.ntptime.DST_in_effect else True
                _man_time = man_time
            case 'time_server':
                ntp_time = self.ntptime.FormattedNTPTime()
                _adjust_timezone = False if self.ntptime.DST_in_effect else True
                _man_time = ntp_time
            case 'system':
                _adjust_timezone = False if self.ntptime.DST_in_effect else True # My guess, not tested in DST...
                system_time= True
        
        tz = self.timezone
        tz += 1 if _adjust_timezone else 0
     
        obj = SmartSunPos(use_system_time=system_time, man_time=_man_time, return_time=True, location=location, timezone=tz, refraction=True)
        azimuth, elevation, returned_time = obj.sun_position
        
        self.Current_angle, self.last_time_checked = [azimuth, elevation], returned_time
        self._memory(store=True)

        elevation = 90 - elevation  if self.adjust_perpendicular_angle_elev else elevation
        azimuth = azimuth - 90 if self.adjust_perpendicular_angle_azim else azimuth
        
        if self.debug: print(f"[{self._classname}] azim: {azimuth}, elev: {elevation}, returned_time: {returned_time}")
        return [azimuth, elevation, returned_time]

    def _ThreadedJob(self):
        while not self._stop_event.is_set():
            if self._stop_event.is_set():
                if self.debug: print(f"[{self._classname}] Thread exitting.")
                for _ in range(self.preferred_long_hold_time):
                    time.sleep(1)
                    if self._stop_event.is_set():
                        break
                return
            
            try:
                self.MALFUNCTION = None
                self.VSINormal()
                self._set_settings(res_thread=True) # Make sure settings are reloaded correctly
                self._memory(load=True, overwrite=True) # Write latest vars to local mem
                while not self._stop_event.is_set():
                    position = self._CalultatePosition() # position = [azim, elev, ret]
                    if position[1] <= 0 or position[1] >= 90: raise ExecutionEnviromentError("Malfunction 12 - OutsideDomainError")
                    calculation_method = self.Calc_cnf

                    if self._stop_event.is_set():
                        if self.debug: print(f"[{self._classname}] Thread going on hold.")
                        break

                    if calculation_method == 'time_based':
                        self._StepperMV(position[0], position[1])
                        for _ in range(self.Calc_val):
                            if self._stop_event.is_set():
                                break
                            time.sleep(1)
                    elif calculation_method == 'degree_based':
                        if self.compare(compare='degree'):
                            self._StepperMV(position[0], position[1])
                        for _ in range(self.preferred_hold_time):
                            if self._stop_event.is_set():
                                break
                            time.sleep(1)
                    elif calculation_method == 'step_based':
                        if self.compare(compare='steps'):
                            self._StepperMV(position[0], position[1])
                        for _ in range(self.preferred_hold_time):
                            if self._stop_event.is_set():
                                break
                            time.sleep(1)
                    else:
                        raise MajorSystemMalfunction('Malfunction 54 - Major System Failure')
    
            
            except Exception as e:
                if self.debug: print(f"[{self._classname}] Malfunction: {e}")
                self.MALFUNCTION = e
                self.VSIError()
                break

            if self.debug: print(f"[{self._classname}] Restarting...")


    def compare(self, compare) -> bool:
        def get_azim_stepper() -> int:
            for i in range(len(self.Steppers)):
                if self.stepperInstances[i].which == 'STX':
                    return i
                
        if compare == 'degree':
            current_angle = self._memory()[2][0]
            current_motor_angle = self.Stepper_save[0]
            if self.debug: print(f"[{self._classname}] comparing (degs) {current_angle} and {current_motor_angle}")
            return True if abs(current_angle - current_motor_angle) >= self.Calc_val \
                or abs(current_angle - current_motor_angle) == self.Calc_val \
                    else False
        elif compare == 'steps':
            current_angle_steps = self.stepperInstances[get_azim_stepper()].get_step(self._memory()[2][0])
            current_motor_step = self.stepperInstances[get_azim_stepper()].get_step(self._memory()[1][0])
            if self.debug: print(f"[{self._classname}] comparing (steps) {current_angle_steps} and {current_motor_step}")
            return True if abs(current_angle_steps - current_motor_step) >= self.Calc_val \
                or abs(current_angle_steps - current_motor_step) == self.Calc_val \
                    else False
        else:
            raise UserError("Malfunction 24 - FaultyParameterError")
        
    def manMove(self, x, y):
        if self.debug: print(f'[{self._classname}] moving to: {x}, {y}')
        self._StepperMV(azim=x, elev=y)
        
        # the next section writes the current cords as they are calculated by the formula.
        # this helps the system recover after a man_cord.
        y = 90 - y  if self.adjust_perpendicular_angle_elev else x
        x = x - 90 if self.adjust_perpendicular_angle_azim else y
        self.Stepper_save = [x, y]
        self._memory(store=True)


    def _StepperMV(self, azim, elev):
        if self._memory()[1] == None:
            self.Stepper_save = [0, 0]
            self._memory(store=True)
        for i in range(len(self.Steppers)):
            try:   
                if self.stepperInstances[i].which == 'STY':
                    self.stepperInstances[i].set_step(step=self.stepperInstances[i].get_step(self._memory()[1][1]))
                    self.stepperInstances[i].goto_specified(elev)
                elif self.stepperInstances[i].which == 'STX':
                    self.stepperInstances[i].set_step(step=self.stepperInstances[i].get_step(self._memory()[1][0]))
                    self.stepperInstances[i].goto_specified(azim)
                else: raise UserError('Malfunction 24 - FaultyParameterError')
            except Exception:
                raise MajorSystemMalfunction('Malfunction 55 - Uncorrected Error ')
        self.Stepper_save = [azim, elev]
        self._memory(store=True)
        return

    def startThreadedJob(self):
        if self.thread and self.thread.is_alive():
            return
        target_function = partial(self._ThreadedJob)
        try:
            self.thread = threading.Thread(target=target_function)
            self.thread.start()
        except Exception:
            raise MajorSystemMalfunction('Malfunction 54 - Major System Malfunction')

    def stopThreadedJob(self):
        if self.thread and self.thread.is_alive():
            self._stop_event.set()
            self.thread.join()
    
    def Restart(self):
        try:
            try:
                self.stopThreadedJob()
                self._stop_event.clear()
                time.sleep(2)
                self.startThreadedJob()
            except:
                raise MajorSystemMalfunction('Malfunction 55 - Uncorrected Error')
        except MajorSystemMalfunction as e:
            self.MALFUNCTION = e
            pass


    #@property
    def CurrentInfo(self):
        return {
            'mantime': self.Man_time,
            'stepper_position': self.Stepper_save,
            'current_calculated_angle': self.Current_angle,
            'last_time_checked': self.last_time_checked,
            'time_source': self.TimeCtr,
            'calculation_method': self.Calc_cnf,
            'calculation_value': self.Calc_val,
            'location': self.Loc_set,
            'status': self._status,
            'timezone': self.timezone
        }
        

    def stop_all(self):
        self.GUtils.global_clearout()

