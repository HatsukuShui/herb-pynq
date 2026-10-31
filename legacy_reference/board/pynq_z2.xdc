# Standalone top ONLY. Based on TUL PYNQ-Z2 mapping; mirror provenance in docs/sources.md.
set_property -dict {PACKAGE_PIN H16 IOSTANDARD LVCMOS33} [get_ports clk125]
create_clock -name clk125 -period 8.000 [get_ports clk125]
set_property -dict {PACKAGE_PIN D19 IOSTANDARD LVCMOS33} [get_ports btn0]
set_property -dict {PACKAGE_PIN R14 IOSTANDARD LVCMOS33} [get_ports {led[0]}]
set_property -dict {PACKAGE_PIN P14 IOSTANDARD LVCMOS33} [get_ports {led[1]}]
set_property -dict {PACKAGE_PIN N16 IOSTANDARD LVCMOS33} [get_ports {led[2]}]
set_property -dict {PACKAGE_PIN M14 IOSTANDARD LVCMOS33} [get_ports {led[3]}]
# Button only enters the asynchronous reset synchronizer, never functional logic.
set_false_path -from [get_ports btn0] -to [get_cells -hier -filter {NAME =~ *u_reset/sync_ff_reg*}]
# LEDs are human-visible indicators with no external synchronous receiver.
set_false_path -to [get_ports {led[*]}]
