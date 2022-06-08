from europi import *
import machine
import time
from europi_script import EuroPiScript

INPUT_GATE_VOLTAGE = 3
OUTPUT_VOLTAGE = 10
MAX_ATTACK = 2000
MAX_RELEASE = 5000


class Envelope:
    def __init__(self, cv_output, eoc_output):
        self.cv_output = cv_output
        self.eoc_output = eoc_output
        self.last_rising = None
        self.last_falling = None
        self.last_end_of_cycle = None
        self.input_gate_high = False
        self.eoc_gate_high = False
        # If the attack stage of the envelope is cut short by the gate, this variable
        # keeps track of the highest value reached so that the release stage can start
        # from the correct value.
        self.highest_value_this_cycle = 0

    def gate_on(self):
        self.last_rising = time.ticks_ms()
        self.input_gate_high = True

    def gate_off(self):
        self.last_falling = time.ticks_ms()
        self.input_gate_high = False

    # Todo: refactor this method
    def update_outputs(self, attack, sustain, release):
        current_time = time.ticks_ms()
        time_since_rising = current_time - (
            self.last_rising if self.last_rising != None else 0
        )
        time_since_falling = current_time - (
            self.last_falling if self.last_falling != None else 0
        )
        time_since_end_of_cycle = current_time - (
            self.last_end_of_cycle if self.last_end_of_cycle != None else current_time
        )
        if self.input_gate_high:
            self.highest_value_this_cycle = min(time_since_rising / attack, 1)
            self.cv_output.voltage(
                OUTPUT_VOLTAGE * sustain * self.highest_value_this_cycle
            )
        else:
            self.cv_output.voltage(
                OUTPUT_VOLTAGE
                * sustain
                * self.highest_value_this_cycle
                * max((release - time_since_falling) / release, 0)
            )
            if (
                self.eoc_gate_high == False
                and time_since_falling >= release
                and time_since_falling < release + attack
            ):
                self.last_end_of_cycle = time.ticks_ms()
                self.eoc_output.on()
                self.eoc_gate_high = True
        if time_since_end_of_cycle >= attack and self.eoc_gate_high:
            self.eoc_output.off()
            self.eoc_gate_high = False


class DualAREnvelope(EuroPiScript):
    def __init__(self):
        # Settings for improved performance
        machine.freq(250_000_000)
        k1.set_samples(32)
        k2.set_samples(32)
        self.envelopes = [
            # Digital input gate
            Envelope(cv1, cv4),
            # Analog input gate
            Envelope(cv3, cv6),
            # Both
            Envelope(cv2, cv5),
        ]
        self.attack = None
        self.sustain = 1
        self.release = None
        self.ui_update_requested = False
        self.load_state()

        @b1.handler
        def reduce_sustain():
            self.sustain = max(self.sustain - 0.05, 0)
            self.ui_update_requested = True
            self.save_state()

        @b2.handler
        def increase_sustain():
            self.sustain = min(self.sustain + 0.05, 1)
            self.ui_update_requested = True
            self.save_state()

    @classmethod
    def display_name(cls):
        return "Dual AR Env."

    def update_ui(self):
        oled.fill(0)
        sustain_width = int(OLED_WIDTH / 4)
        sustain_height = int(OLED_HEIGHT * self.sustain)
        attack_width = int(
            (OLED_WIDTH - sustain_width) * self.attack / (MAX_ATTACK + MAX_RELEASE)
        )
        release_width = int(
            (OLED_WIDTH - sustain_width) * self.release / (MAX_ATTACK + MAX_RELEASE)
        )
        oled.line(0, OLED_HEIGHT, attack_width, OLED_HEIGHT - sustain_height, 1)
        oled.hline(attack_width, OLED_HEIGHT - sustain_height, sustain_width, 1)
        oled.line(
            attack_width + sustain_width,
            OLED_HEIGHT - sustain_height,
            attack_width + sustain_width + release_width,
            OLED_HEIGHT,
            1,
        )
        oled.show()
        self.ui_update_requested = False

    def save_state(self):
        settings = {"s": self.sustain}
        self.save_state_json(settings)

    def load_state(self):
        settings = self.load_state_json()
        if "s" in settings:
            self.sustain = settings["s"]

    def update_settings(self):
        new_attack = k1.percent() * MAX_ATTACK + 1
        new_release = k2.percent() * MAX_RELEASE + 1
        if not (new_attack == self.attack and new_release == self.release):
            self.attack = new_attack
            self.release = new_release
            self.ui_update_requested = True

    def play(self):
        new_first_gate_high = din.value() > 0
        analog_input = ain.read_voltage()
        new_second_gate_high = analog_input > INPUT_GATE_VOLTAGE or (
            self.envelopes[1].input_gate_high
            and analog_input > INPUT_GATE_VOLTAGE - 0.1
        )
        new_third_gate_high = new_first_gate_high or new_second_gate_high
        if new_first_gate_high != self.envelopes[0].input_gate_high:
            if new_first_gate_high:
                self.envelopes[0].gate_on()
            else:
                self.envelopes[0].gate_off()
        if new_second_gate_high != self.envelopes[1].input_gate_high:
            if new_second_gate_high:
                self.envelopes[1].gate_on()
            else:
                self.envelopes[1].gate_off()
        if new_third_gate_high != self.envelopes[2].input_gate_high:
            if new_third_gate_high:
                self.envelopes[2].gate_on()
            else:
                self.envelopes[2].gate_off()
        for envelope in self.envelopes:
            envelope.update_outputs(self.attack, self.sustain, self.release)

    def main(self):
        while True:
            self.update_settings()
            if self.ui_update_requested:
                self.update_ui()
            self.play()


# Main script execution
if __name__ == "__main__":
    DualAREnvelope().main()
