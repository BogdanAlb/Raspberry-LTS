import hx711 from HX711

hx = HX711(dout=5, pd_sck=6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(92)
hx.reset()
hx.tare()       
print(hx.get_weight(5))
hx.power_down()
hx.power_up()

# Path: HX711.py
import RPi.GPIO as GPIO