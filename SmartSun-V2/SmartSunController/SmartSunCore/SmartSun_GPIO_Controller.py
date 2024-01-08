# Imports
import sys
import time
import RPi.GPIO as GPIO

# Exceptions
class StepperDomainError(Exception):
    pass

class StepperExecutionError(Exception):
    pass

# Class
class stepper_controller():
    def __init__(self, pins: tuple[int, int, int, int], steps: int = 4096, which: str = None, debug: bool = False):
        self.which = which # STX/STY
        self._debug = debug
        self._pins = pins
        self._steps = steps
        self._step = 0   # int: 0 - 4096
        self._stepdegree = 360/self._steps
        self._phase = 0
        self._hold = self.set_desired_hold_time()
        self._seq = [
            [1, 0, 0, 1],
            [1, 0, 0, 0],
            [1, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 1],
            [0, 0, 0, 1]]
            
        self._GPIO_setup()
    
    @property
    def _classname(self):
        return self.__class__.__name__

    def set_step(self, step):
        self._step = step
        return       

    def set_desired_hold_time(self) -> float:
        return 0.005

    def GPIO_clearout(self):
        GPIO.setmode(GPIO.BCM)
        for pin in self._pins:
            GPIO.setup(pin, GPIO.IN)
            GPIO.setup(pin, GPIO.LOW)
        GPIO.cleanup()

    def _GPIO_setup(self) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        for pin in self._pins:
            if self._debug: print(f"[{self._classname}] Setting up pin {pin}...")
            GPIO.setup (pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
            

    def return_default(self):
        self.goto_specified(0)

    def goto_specified(self, angle):
        if self.which == 'STY': domain = [0, 90]
        elif self.which == 'STX': domain = [0, 360]

        def get_closest_dir(angle):
            current_step = self._step
            goto_step = self.get_step(angle)
            a = int(goto_step - current_step)
            b = int(self._steps - (goto_step - current_step))
            if a < b:
                return 'cw'
            else:
                return 'ccw'

        try:
            if ((domain[0] <= angle) and (angle <= domain[1])):
                goto_step = self.get_step(angle)
                requested_steps_cw = int(goto_step - self._step)           
                requested_steps_ccw = int(self._steps - (goto_step - self._step))
                
                dir = get_closest_dir(angle)

                if requested_steps_cw < 0:
                    requested_steps = int(-1 * requested_steps_cw)
                    dir = 'ccw'
                    if self._debug: print(f'[{self._classname}] --Step NEG-CW--')
                elif requested_steps_ccw < 0:
                    requested_steps = int(-1 * requested_steps_ccw)
                    dir = 'cw'
                    if self._debug: print(f'[{self._classname}] --Step NEG-CCW--')
                else: 
                    if dir == 'cw': 
                        requested_steps = requested_steps_cw
                        if self._debug: print(f'[{self._classname}]  --Step CW--')
                    else: 
                        requested_steps = requested_steps_ccw
                        if self._debug: print(f'[{self._classname}]  --Step CCW--')
                

                if self._debug: print(f"""[{self._classname}] INCOMMING DATA:
[{self._classname}] Selected_stepper: {self.which}
[{self._classname}] Requested_angle: {angle}
[{self._classname}] Requested_direction: {dir}
[{self._classname}] Current_angle: {self.get_angle()}
[{self._classname}] Requested_steps: {requested_steps}\n""")
                
                for _ in range(requested_steps):
                    self._make_step(dir)

            else:
                raise StepperDomainError("StepperDomainError: The value specified is not in the domain supported by this machine.")
        
        except StepperExecutionError as e:
            print("StepperExecutionError: There has been some trouble processing the given data.")
            exit()


    
    def get_step(self, angle: float) -> int:
        return int(((self._steps/360) * angle))

    
    def get_angle(self, steps: int = None) -> float:
        step = self._step if steps == None else steps
        return (360/self._steps) * step # calculate angle

    def _make_step(self, dir: str) -> bool:
        def check_domain():
            if self._step > (self._steps - 1): self._step = 0
            elif self._step < 0: self._step = (self._steps - 1)

        try:
            check_domain()
            match dir.lower():
                case 'cw':
                    self._phase = ((self._step + 1) % 8)
                    self._step += 1
                case 'ccw':
                    self._phase = ((self._step - 1) % 8)
                    self._step -= 1

            for pin in self._pins:
                GPIO.output(pin, self._seq[self._phase][self._pins.index(pin)])
                time.sleep(self._hold)

            return True

        except StepperExecutionError as e:
            print("StepperExecutionError: The has been some trouble processing the given data.")
            exit()