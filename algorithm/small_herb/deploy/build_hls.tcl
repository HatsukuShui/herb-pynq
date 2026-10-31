# Run in Vivado HLS / traditional Vitis HLS after setting the actual full part.
if {![info exists ::env(FPGA_PART)] || ![string match "xc7z020*" $::env(FPGA_PART)]} {
    error "Set FPGA_PART to the full part name from the actual ZYNQ-7020 board project."
}
set root [file dirname [file normalize [info script]]]
cd $root
set top small_lr_q
if {[info exists ::env(SMALL_TOP)]} { set top $::env(SMALL_TOP) }
if {$top ni {small_lr_q small_mlp_q}} { error "SMALL_TOP must be small_lr_q or small_mlp_q" }
set testflag -DSMALL_HLS_LR
if {$top eq "small_mlp_q"} { set testflag -DSMALL_HLS_MLP }
# Preserve generated projects; use a new HLS_RUN_NAME for a fresh build.
set project ${top}_project
if {[info exists ::env(HLS_RUN_NAME)]} { set project $::env(HLS_RUN_NAME) }
if {[file exists $project]} { error "Project exists. Choose a new HLS_RUN_NAME." }
open_project $project
set_top $top
add_files [file join $root small_hls.cpp] -cflags "-I$root"
add_files -tb [file join $root tb_small.cpp] -cflags "-I$root $testflag"
open_solution solution1
set_part $::env(FPGA_PART)
create_clock -period 10 -name default
csim_design
csynth_design
cosim_design -rtl verilog
export_design -format ip_catalog
exit
