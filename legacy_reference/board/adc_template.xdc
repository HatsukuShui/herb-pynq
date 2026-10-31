# NOT loaded by build. ADC model, connector and timing remain unknown.
# Example PMOD A assignment from board map, enable only after actual wiring is confirmed:
# CS=Y18 (pin1), MOSI=Y19 (pin2), MISO=Y16 (pin3), SCLK=Y17 (pin4).
# set_property -dict {PACKAGE_PIN Y18 IOSTANDARD LVCMOS33} [get_ports adc_cs_n]
# set_property -dict {PACKAGE_PIN Y19 IOSTANDARD LVCMOS33} [get_ports adc_mosi]
# set_property -dict {PACKAGE_PIN Y16 IOSTANDARD LVCMOS33} [get_ports adc_miso]
# set_property -dict {PACKAGE_PIN Y17 IOSTANDARD LVCMOS33} [get_ports adc_sclk]
# Add generated clock and min/max input/output delays from ADC datasheet + PCB delays.
# Never suppress UCIO/NSTD/TIMING DRC to force a bitstream.
