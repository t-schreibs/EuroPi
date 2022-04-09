# Hocketer

author: Tyler Schreiber (github.com/t-schreibs)

date: 2022-04-09

labels: triggers, drums, randomness, voice allocation

Stripped-down EuroPi note hocketer / voice allocator loosely inspired by the Intellijel Shifty module, but with its own take on randomization.



In music, a 'hocket' (often spelled a variety of ways) happens when two or more voices share a bit of melodic content, alternately playing portions of it in such a way that the melody is continuous even when all but a single player are at rest. Usually, each voice will perform only a handful of notes at a time (sometimes as few as a single note), and so the alternation occurs rapidly.

This program allows you to input a sequence - in the form of gate + CV - into the EuroPi and output that sequence to three voices, allocating notes in such a way that the entire sequence is performed continuously, but shared across the different voices.

Credits:
- The Europi hardware and firmware was designed by Allen Synthesis: https://github.com/Allen-Synthesis/EuroPi

# Controls

- digital_in: gate in
- analog_in: pitch (or other CV) in

- knob_1: set number of steps to be performed per voice
- knob_2: set the directionality of the progression through the voices

- button_1: rotate the voices
- button_2: toggle randomization of the number of steps to be performed per voice

- output_1: voice 1 gate
- output_2: voice 2 gate
- output_3: voice 3 gate
- output_4: voice 1 pitch (or other CV)
- output_5: voice 2 pitch (or other CV)
- output_6: voice 3 pitch (or other CV)

# Getting started

## Basic usage

Connect a gate + CV sequence of some kind to the EuroPi inputs, with the gate connected to the digital input and the CV connected to the analog input. Hocketer will start to split it among its 3 voices:
- Voice one
    - Gate: CV1
    - Pitch/CV: CV4
- Voice two
    - Gate: CV2
    - Pitch/CV: CV5
- Voice three
    - Gate: CV3
    - Pitch/CV: CV6

Knob 1 controls the amount of steps each voice will perform before the sequence is moved to the next voice. It ranges from 1 to 16 steps. Start by turning it fully counter-clockwise, so that only one step is performed at a time.
Knob 2 controls the directionality of the motion between the voices, or the likelihood that Hocketer will pick the voice in that direction as the next voice. This is easier to visualize than explain, and is easier to see when knob 1 is turned fully counter-clockwise. As you turn knob 2 to the left from center, watch as the progression of the voices becomes less random and more clearly leftward. The same is true as you turn it right of center, while at center progression of the voices is fully random.

## Further usage

The two buttons do interesting things as well! Button 1 rotates the voices (this often results in a voice getting skipped or repeated, depending on the directionality set by knob 2). Button 2 toggles randomization of the amount of steps each voice performs. When randomization is on, knob 1 functions as an attenuator for the randomization.