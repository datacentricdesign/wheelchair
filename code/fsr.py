import RPi.GPIO as GPIO #GPIO for mux selection
import Adafruit_ADS1x15 #AD converter

class FSR():
    def __init__(self, number_fsr):
        self.number_fsr = number_fsr
        if number_fsr > 0:
            # sensor value array
            self.fsr_values = [0] * number_fsr
            self.ad_chanel = 0 # ad chanel
            # we connect mux 4 pins to 5,6,14,19, feel free to change
            self.mux_pins = [5,6,14,19]
            
            # adc setup
            self.adc = self.set_up_fsr(self.ad_chanel, self.mux_pins)

            # array for mux address, 4 pins, 16 channels 
            self.mux_selection    = [[0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1]]*4 
            self.mux_selection[1] =  [0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1] 
            self.mux_selection[2] =  [0,0,0,0,1,1,1,1,0,0,0,0,1,1,1,1] 
            self.mux_selection[3] =  [0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1] 
    
    def set_up_fsr(self):
        self.adc = Adafruit_ADS1x15.ADS1115() #pls check ADS1115
        GAIN = 1 #pls check ADS1115
        self.adc.start_adc(self.ad_chanel, gain=GAIN) #pls check ADS1115
        GPIO.setmode(GPIO.BCM)  # use BCM layout, check Raspberry Pi
        GPIO.setwarnings(False) # disable warnings
        for each in self.mux_pins:   # all mux pin in output mode
            GPIO.setup(each, GPIO.OUT)
        return self.adc # return the handle of adc

    def read_fsrs(self):
        fsr_values = [0]*self.nu # array of fsr values
        for chanel in range(0,self.number_fsr):  # for each chanel
            for pin_index in range (0,4): # set the ri9ght selection
                GPIO.output(self.mux_pins[pin_index], self.mux_selection[pin_index][chanel])
            #time.sleep(0.001) # for stable input, you can also delete it
            fsr_values[chanel] = self.adc.get_last_result() # AD converstion 
        return fsr_values