from europi import *
import machine
from europi_script import EuroPiScript
from time import ticks_ms
from random import randint

'''
Hocketer
author: Tyler Schreiber (github.com/t-schreibs)
date: 2022-04-09
labels: triggers, drums, randomness, voice allocation

Stripped-down EuroPi note hocketer / voice allocator loosely inspired by the
Intellijel Shifty module, but with its own take on randomization.
'''

# Class to group cv outputs by voice
class Voice:
    def __init__(self, gate_output: Output, pitch_output: Output):
        self.gate_output = gate_output
        self.pitch_output = pitch_output
    def on(self):
        self.gate_output.on()
    def off(self):
        self.gate_output.off()
    def set_pitch(self, voltage):
        self.pitch_output.voltage(voltage)

class Hocketer(EuroPiScript):
    def __init__(self):
        # Settings for improved performance.
        machine.freq(250_000_000)
        k1.set_samples(32)
        k2.set_samples(32)        
        self.voices = [
            Voice(cv1, cv4),
            Voice(cv2, cv5),
            Voice(cv3, cv6)
            ]
        self.pulses_per_voice = 1
        self.pulses_since_last_voice = 0
        self.current_voice = 0
        self.voice_rotate_requested = False
        self.random_pulses_per_voice = False
        self.directionality_of_voice_order = 0
        
        @din.handler
        def gate_on():
            # The sequence will move to another voice when the amount
            # of pulses at the current voice has met or exceeded the
            # "pulses per voice" value
            if self.pulses_since_last_voice >= self.pulses_per_voice:
                self.current_voice = self.get_next_voice()
                self.pulses_since_last_voice = 0
                # If the "pulses per voice" value is randomized, a new value
                # is obtained before the next voice begins to play, with k1
                # acting as an attenuator on the randomization
                if self.random_pulses_per_voice:
                    self.pulses_per_voice = randint(1, k1.read_position(16))
            self.voices[self.current_voice].on()
            self.pulses_since_last_voice += 1
            
        @din.handler_falling
        def gate_off():
            self.voices[self.current_voice].off()
            # Voices are rotated only once the current gate has closed,
            # to prevent hangups
            if self.voice_rotate_requested:
                self.voices = self.rotate(self.voices)
                self.voice_rotate_requested = False
            
        @b1.handler
        def request_voice_rotation():
            # This request is fulfilled once the current gate has closed
            self.voice_rotate_requested = True
            
        @b2.handler
        def toggle_random_pules_per_voice():
            self.random_pulses_per_voice = not self.random_pulses_per_voice
        
    def rotate(self, items):
        return items[1:] + items[:1]
    
    def get_next_voice(self):
        # Directionality determines the likelihood that the next voice will
        # be either the voice to the left or the voice to the right of the
        # current voice - at 100, it will always progress to the voice to 
        # the right; at 0, it will always progress to the voice to the left; 
        # at 50, it might move either direction
        if randint(0, 100) <= self.directionality_of_voice_order:
            if self.current_voice >= len(self.voices) - 1:
                return 0
            else:
                return self.current_voice + 1
        else:
            if self.current_voice <= 0:
                return len(self.voices) - 1
            else:
                return self.current_voice - 1
            
    def show_ui(self):
        oled.centre_text(str(self.pulses_since_last_voice) + "/" +
            ("?" if self.random_pulses_per_voice
                 else str(self.pulses_per_voice)) +
            "\n" + (str((self.directionality_of_voice_order - 50) * 2) + "% right"
            if self.directionality_of_voice_order > 50
            else (str(100 - self.directionality_of_voice_order * 2) + "% left"
                if self.directionality_of_voice_order < 50
                else "0%")))
    
    def main(self):
        while True:
            # Only change the "pulses per voice" value if it is not
            # currently being randomized
            if not self.random_pulses_per_voice:
                self.pulses_per_voice = k1.read_position(16) + 1
            self.directionality_of_voice_order = k2.read_position(21) * 5
            self.voices[self.current_voice].set_pitch(ain.read_voltage())
            self.show_ui()
        
# Main script execution
if __name__ == '__main__':
    Hocketer().main()