"""Micropython module for stepper motor driven by Easy Driver."""
from machine import Pin
from time import sleep_us


class Stepper:
   
    def _init_(self, step_pin, dir_pin, sleep_pin):
        """Initialise stepper."""
        self.stp = Pin(step_pin, Pin.OUT)
        self.dir = Pin(dir_pin, Pin.OUT)
        self.slp = Pin(sleep_pin, Pin.OUT)

        self.step_time = 10  # us for ESP32, reduced step time
        self.steps_per_rev = 1600
        self.current_position = 0

    def power_on(self):
        """Power on stepper."""
        self.slp.value(1)

    def power_off(self):
        """Power off stepper."""
        self.slp.value(0)
        # Optionally, reset the position, depends on use case
        # self.current_position = 0

    def steps(self, step_count):
        """Rotate stepper for given steps."""
        if step_count == 0:
            return  # No steps, exit early
        self.dir.value(0 if step_count > 0 else 1)
        for _ in range(abs(step_count)):
            self.stp.value(1)
            sleep_us(self.step_time)
            self.stp.value(0)
            sleep_us(self.step_time)
        self.current_position += step_count

    def rel_angle(self, angle):
        """Rotate stepper for given relative angle."""
        steps = int(angle / 360 * self.steps_per_rev)
        self.steps(steps)

    def abs_angle(self, angle):
        """Rotate stepper for given absolute angle since last power on."""
        target_steps = int(angle / 360 * self.steps_per_rev)
        step_difference = target_steps - (self.current_position % self.steps_per_rev)
        self.steps(step_difference)

    def revolution(self, rev_count):
        """Perform given number of full revolutions."""
        self.steps(rev_count * self.steps_per_rev)

    def set_step_time(self, us):
        """Set time in microseconds between each step."""
        # Minimum step time for ESP32 is around 10 us
        self.step_time = max(10, us)