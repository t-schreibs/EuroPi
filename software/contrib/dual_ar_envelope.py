from black import out
from europi import *
import machine
import time
from europi_script import EuroPiScript

INPUT_GATE_VOLTAGE = 3
GATE_VOLTAGE = 5
MAX_ATTACK = 2000
MAX_RELEASE = 5000


class Envelope:
    def __init__(self, outputs):
        self.outputs = outputs
        self.last_triggered = None
        self.gate_high = False

    def gate_on(self):
        self.last_triggered = time.ticks_ms()
        self.gate_high = True

    def gate_off(self):
        self.last_triggered = time.ticks_ms()
        self.gate_high = False

    def update_outputs(self, attack, sustain, release):
        time_since_trigger = time.ticks_ms() - self.last_triggered
        if self.gate_high:
            voltage = GATE_VOLTAGE * sustain * min(time_since_trigger / attack, 1)
        else:
            voltage = (
                GATE_VOLTAGE * sustain * max(release - time_since_trigger / release, 0)
            )
        for output in self.outputs:
            output.voltage(voltage)


class MoltQuantizer(EuroPiScript):
    def __init__(self):
        # Settings for improved performance.
        machine.freq(250_000_000)
        k1.set_samples(32)
        k2.set_samples(32)
        self.envelopes = [
            Envelope([cv1, cv4, cv2, cv5]),
            Envelope([cv3, cv6, cv2, cv5]),
        ]
        self.attack = None
        self.sustain = None
        self.release = None
        self.ui_update_requested = False
        self.load_state()

        @b1.handler
        def reduce_sustain():
            self.sustain = max(self.release - 0.1, 0)
            self.ui_update_requested = True

        @b2.handler
        def increase_sustain():
            self.sustain = min(self.release + 0.1, 1)
            self.ui_update_requested = True

    @classmethod
    def display_name(cls):
        return "Dual AR Env."

    def update_ui(self):
        oled.centre_text(
            "A: "
            + self.attack
            + "\nR: "
            + self.release
            + "\nAttenuation: "
            + self.sustain
        )
        self.ui_update_requested = False

    def save_state(self):
        settings = {"s": self.sustain}
        self.save_state_json(settings)

    def load_state(self):
        settings = self.load_state_json()
        if "s" in settings:
            self.sustain = settings["s"]

    def update_settings(self):
        new_attack = k1.percent() * MAX_ATTACK
        new_release = k2.percent() * MAX_RELEASE
        if not (new_attack == self.attack and new_release == self.release):
            self.attack = new_attack
            self.release = new_release
            self.ui_update_requested = True

    def play(self):
        new_first_gate_high = din.value() > 0
        new_second_gate_high = ain.read_voltage() > INPUT_GATE_VOLTAGE
        if new_first_gate_high != self.envelopes[0].gate_high:
            if new_first_gate_high:
                self.envelopes[0].gate_on()
            else:
                self.envelopes[0].gate_off()
        if new_second_gate_high != self.envelopes[1].gate_high:
            if new_second_gate_high:
                self.envelopes[1].gate_on()
            else:
                self.envelopes[1].gate_off()
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
    MoltQuantizer().main()
