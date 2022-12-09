import random
from europi import *
import machine
import math
from europi_script import EuroPiScript

NOTES = {
    0: "C",
    1: "C#",
    2: "D",
    3: "D#",
    4: "E",
    5: "F",
    6: "F#",
    7: "G",
    8: "G#",
    9: "A",
    10: "A#",
    11: "B",
}


class Scale:
    def __init__(self, name, intervals):
        self.name = name
        self.intervals = intervals


class ChordDefinition:
    def __init__(self, name, bass_voltage_offsets, treble_voltage_offsets, is_advanced):
        self.name = name
        self.bass_voltage_offsets = bass_voltage_offsets
        self.treble_voltage_offsets = treble_voltage_offsets
        self.is_advanced = is_advanced


class Voice:
    def __init__(self, min_pitch, max_pitch, cv_output: Output):
        self.min_pitch = min_pitch
        self.max_pitch = max_pitch
        self.current_pitch = 0
        self.cv_output = cv_output

    def set(self, value):
        self.cv_output.voltage(value)
        self.current_pitch = value

    def get_current_note_name(self):
        note, octave = math.modf(self.current_pitch)
        return NOTES[round(note * 12)] + str(int(octave))


class VoiceLeader(EuroPiScript):
    def __init__(self):
        # Settings for improved performance
        machine.freq(250_000_000)
        k1.set_samples(256)
        k2.set_samples(256)
        self.bass_voice = Voice(1, 3, cv4)
        self.treble_voices = [
            Voice(2, 4, cv1),
            Voice(3, 5, cv2),
            Voice(4, 6, cv3),
        ]
        self.chords = [
            ChordDefinition(
                "Maj. triad", (0, 4 / 12, 7 / 12), (0, 4 / 12, 7 / 12), False
            ),
            ChordDefinition(
                "Min. triad", (0, 3 / 12, 7 / 12), (0, 3 / 12, 7 / 12), False
            ),
            ChordDefinition(
                "Dim. triad", (0, 3 / 12, 6 / 12), (0, 3 / 12, 6 / 12), False
            ),
            ChordDefinition(
                "Aug. triad", (0, 4 / 12, 8 / 12), (0, 4 / 12, 8 / 12), False
            ),
            ChordDefinition(
                "Maj. 7th", (0, 4 / 12, 11 / 12), (0, 4 / 12, 7 / 12), True
            ),
            ChordDefinition(
                "Min. 7th", (0, 3 / 12, 10 / 12), (0, 3 / 12, 7 / 12), True
            ),
            ChordDefinition(
                "Dom. 7th", (0, 4 / 12, 10 / 12), (0, 4 / 12, 7 / 12), True
            ),
            ChordDefinition(
                "Fully dim. 7th", (0, 3 / 12, 9 / 12), (0, 3 / 12, 6 / 12), True
            ),
        ]
        self.scales = [
            Scale("CHROM", (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)),
            Scale("MAJOR", (0, 2, 4, 5, 7, 9, 11)),
            Scale("HARM ", (0, 2, 3, 5, 7, 8, 11)),
            Scale("MEL  ", (0, 2, 3, 5, 7, 9, 11)),
        ]
        self.current_key = None
        self.current_scale = 0
        self.current_root = None
        self.current_chord = None
        self.ui_update_requested = True
        self.save_state_requested = False
        self.root_inversions_only = False
        self.get_root_from_analog_input = False
        self.load_state()

        @b1.handler
        def turn_on_root_inversions_only():
            self.root_inversions_only = True
            self.ui_update_requested = True

        @b1.handler_falling
        def turn_off_root_inversions_only():
            self.root_inversions_only = False
            self.ui_update_requested = True

        @b2.handler
        def toggle_get_root_from_analog_input():
            self.get_root_from_analog_input = not self.get_root_from_analog_input
            self.save_state_requested = True
            self.ui_update_requested = True

    def get_current_scale_notes(self, key, scale):
        return map(lambda n: (key + n) % 12, self.scales[scale].intervals)

    def get_is_chord_in_key(self, available_notes, root_note, chord: ChordDefinition):
        return all(
            map(
                lambda o: ((root_note + o) % 12) in available_notes,
                # Don't need to check the root note, so remove it.
                chord.treble_voltage_offsets[1:],
            )
        )

    def get_valid_chords(self, root_note):
        notes = self.get_current_scale_notes(self.current_key, self.current_scale)
        return filter(
            lambda c: self.get_is_chord_in_key(notes, root_note, c), self.chords
        )

    def get_next_chord(self, root_note):
        chords = self.get_valid_chords(root_note)
        if len(chords) > 0:
            return chords[random.randint(0, len(chords) - 1)]
        else:
            # Defaulf if no chords match (should be an impossibility if the chord
            # lists are set up correctly)
            return ChordDefinition("Octaves", (0,), (0,), False)

    def save_state(self):
        settings = {"i": self.get_root_from_analog_input}
        self.save_state_json(settings)
        self.save_state_requested = False

    def load_state(self):
        settings = self.load_state_json()
        if "a" in settings:
            self.get_root_from_analog_input = settings["a"]

    def update_ui(self):
        oled.fill(0)
        padding = 5
        treble_voice_count = len(self.treble_voices)
        voice_width = int(OLED_WIDTH / treble_voice_count)
        voice_height = int(OLED_HEIGHT / 2)
        # Note names for treble voices
        for voice in self.treble_voices:
            i = self.treble_voices.index(voice)
            left_side = i * voice_width
            oled.rect(left_side, 0, left_side + voice_width, voice_height, 1)
            oled.text(voice.get_current_note_name(), left_side + padding, padding, 1)
        # Note name for bass voice
        oled.rect(0, voice_height, voice_width, OLED_HEIGHT, 1)
        oled.text(
            self.bass_voice.get_current_note_name(), padding, voice_height + padding
        )
        # Settings
        oled.text(
            "{:<2}".format(NOTES[self.current_key])
            + "|"
            + self.scales[self.current_scale].name
            + ("|A" if self.get_root_from_analog_input else "|D"),
            voice_width + padding,
            voice_height + padding,
        )
        oled.show()

    def update_settings(self):
        new_key = k1.range(12)
        if self.current_key != new_key:
            self.current_key = new_key
            self.ui_update_requested = True
        new_scale = k2.range(len(self.scales))
        if self.current_scale != new_scale:
            self.current_scale = new_scale
            self.ui_update_requested = True

    def main(self):
        while True:
            # actually run code here ((()))
            self.update_settings()
            if self.ui_update_requested:
                self.update_ui()
            if self.save_state_requested:
                self.save_state()


# Main script execution
if __name__ == "__main__":
    VoiceLeader().main()
