from europi import *
from time import ticks_diff, ticks_ms, sleep
from random import randint, uniform
from europi_script import EuroPiScript
import machine

'''
Probapoly
author: Nik Ansell (github.com/gamecat69)

A polyrhythmic sequencer with probability

digital_in: Clock input
analog_in: Different mode, adjusted by setting self.ainMode as follows:
- Mode 1: Analogue input toggles double time feature
- Mode 2: Analogue input voltage adjusts the upper poly value
- [default] Mode 3: Analogue input voltage adjusts the probabilities of outputs 2,3,5,6 sending gates

button_1: Short press (<500ms): Reduce pattern length (using manual pattern length is ON). Long Press (>500ms): Toggle doubletime feature
button_2: Short press (<500ms): Reduce pattern length (using manual pattern length is ON). Long Press (>500ms): Toggle Manual pattern length feature

knob_1: Select upper polyrhythm value
knob_2: Select lower polyrhythm value

output_1: Gate upper polyrhythm
output_2: Gate upper polyrhythm (50% probability)
output_3: Gate upper polyrhythm (25% probability)
output_4: Gate lower polyrhythm
output_5: Gate lower polyrhythm (50% probability)
output_6: Gate lower polyrhythm (50% probability)

'''

class Poly(EuroPiScript):
    def __init__(self):
        
        # Needed if using europi_script
        super().__init__()

        # Overclock the Pico for improved performance.
        machine.freq(250_000_000)

        # Variables
        self.step = 1
        self.clockStep = 0
        self.resetTimeout = 2000
        self.maxPolyVal = 23
        self.upper = 1
        self.lower = 3
        self.ainValue = 0
        self.upperBernoulliProb = 50
        self.lowerBernoulliProb = 50
        self.upperProb1 = 50
        self.upperProb2 = 25
        self.lowerProb1 = 50
        self.lowerProb2 = 25
        self.doubleTime = False
        self.doubleTimeManualOverride = False
        self.manualPatternLength = False
        self.patternLength = self.lcm(self.upper, self.lower)
        self.patternLengthPrevious = self.patternLength
        
        # Todo: Make this mode accessible from the UI
        # Mode 1: Analogue input toggles double time feature
        # Mode 2: Analogue input voltage adjusts the upper poly value
        # Mode 3: Analogue input voltage adjusts the probabilities of outputs 2,3,5,6 sending gates
        self.ainMode = 3

        @din.handler
        def clockRising():
            for cv in cvs:
                cv.off()
            #self.updateScreen()
            self.handleClock()
            self.clockStep +=1
            self.step += 1

            # Reached of of pattern, or a shorter patter is now needed, reset step to 0
            if self.step >= self.patternLength + 1:
                self.step = 1

        @din.handler_falling
        def clockFalling():
            for cv in cvs:
                cv.off()
            if self.doubleTimeManualOverride or self.doubleTime:
                #self.updateScreen()
                self.handleClock()
                self.clockStep +=1
                self.step += 1

                # Reached of of pattern, or a shorter patter is now needed, reset step to 0
                if self.step >= self.patternLength + 1:
                    self.step = 1

        @b1.handler_falling
        def b1Pressed():
            if ticks_diff(ticks_ms(), b1.last_pressed()) >  500 and ticks_diff(ticks_ms(), b2.last_pressed()) < 3000:
                # toggle double-time feature
                self.doubleTimeManualOverride = not self.doubleTimeManualOverride
            else:
                # Decrement pattern length by 1
                self.patternLength -= 1
                # Set the pattern length to the previous value for playability
                self.patternLengthPrevious = self.patternLength

        @b2.handler_falling
        def b1Pressed():
            if ticks_diff(ticks_ms(), b2.last_pressed()) >  500 and ticks_diff(ticks_ms(), b2.last_pressed()) < 3000:
                self.manualPatternLength = not self.manualPatternLength
                if self.manualPatternLength:
                    # Set the pattern length to the previous value for playability, or 32 if not set previously (un changed)
                    if self.patternLengthPrevious == self.patternLength:
                        self.patternLength
                    else:
                        self.patternLength = self.patternLengthPrevious
            else:
                # Increment pattern length by 1
                self.patternLength += 1
                # Set the pattern length to the previous value for playability
                self.patternLengthPrevious = self.patternLength

    def handleClock(self):
        
        # Play upper gate
        if self.step == 1 or (self.step-1) % self.upper == 0:
            cv1.value(1)

        # Output trigger with fixed and unrelated probabilities
            if randint(0,99) < self.upperProb1:
                cv2.value(1)

            if randint(0,99) < self.upperProb2:
                cv3.value(1)

        # Play lower gate
        if self.step == 1 or (self.step-1) % self.lower == 0:
            cv4.value(1)

            # Output trigger with fixed and unrelated probabilities
            if randint(0,99) < self.lowerProb1:
                cv5.value(1)

            if randint(0,99) < self.lowerProb2:
                cv6.value(1)

    # Generate pattern length by finding the lowest common multiple (LCM) and greatest common divisor (GCD)
    # https://www.programiz.com/python-programming/examples/lcm
    def lcm(self, x, y):
        return (x*y)//self.computeGcd(x,y)

    def computeGcd(self, x, y):
        while(y):
            x, y = y, x % y
        return x

    def getUpper(self):
        # Mode 2, use the analogue input voltage to set the upper ratio value
        if self.ainValue > 0.9 and self.ainMode == 2:
            self.upper = int((self.maxPolyVal / 100) * self.ainValue) + 1
        else:
            self.upper = k1.read_position(self.maxPolyVal) + 1

    def getLower(self):
        self.lower = k2.read_position(self.maxPolyVal) + 1

    def getAinValue(self):
        self.ainValue = 100 * ain.percent()
        #print(self.ainValue)

    def updateScreen(self):
        # Clear the screen
        oled.fill(0)

        rectLeftX = 20
        rectRightX = 44
        rectLength = 20
 
        # Calculate where the steps should be using left justification
        if self.step <= 9:
            stepLeftX = 86
        elif self.step > 9 and self.step <= 99:
            stepLeftX = 78
        else:
            stepLeftX = 70

        # current step
        oled.text(str(self.step) + '|' + str(self.patternLength), stepLeftX, 0, 1)

        # Upper + lower values
        oled.text(str(self.upper), 0, 6, 1)
        oled.rect(0 , 17, 16, 1, 1)
        oled.text(str(self.lower), 0, 22, 1)

        # probabilities
        oled.rect(rectLeftX, 6, rectLength, 8, 1)
        oled.fill_rect(rectLeftX, 6, self.upperProb1//5, 8, 1)
        oled.rect(rectRightX, 6, rectLength, 8, 1)
        oled.fill_rect(rectRightX, 6, self.upperProb2//5, 8, 1)
        oled.rect(rectLeftX, 22, rectLength, 8, 1)
        oled.fill_rect(rectLeftX, 22, self.lowerProb1//5, 8, 1)
        oled.rect(rectRightX, 22, rectLength, 8, 1)
        oled.fill_rect(rectRightX, 22, self.lowerProb2//5, 8, 1)

        if self.doubleTimeManualOverride or self.doubleTime:
            oled.text('!¿', 100, 22, 1)
        if self.manualPatternLength:
            oled.text('M', 119, 22, 1)
        oled.show()

    def main(self):
        while True:
            self.getLower() 
            self.getUpper()
            self.getAinValue()
            self.updateScreen()

            # Ain CV toggles doubleTime feature
            if self.ainMode == 1:
                if self.ainValue > 10:
                    self.doubleTime = True
                else:
                    self.doubleTime = False
            # Ain CV controls probability
            elif self.ainValue >= 0.9 and self.ainMode == 3:
                self.upperProb1 = int(self.ainValue * 2)
                self.upperProb2 = int(self.ainValue * 1)
                self.lowerProb1 = int(self.ainValue * 2)
                self.lowerProb2 = int(self.ainValue * 1)

            if not self.manualPatternLength:
                self.patternLength = self.lcm(self.upper, self.lower)

            # If I have been running, then stopped for longer than reset_timeout, reset the steps and clock_step to 0
            if self.clockStep != 0 and ticks_diff(ticks_ms(), din.last_triggered()) > self.resetTimeout:
                self.step = 1
                self.clockStep = 0

if __name__ == '__main__':
    dm = Poly()
    dm.main()

