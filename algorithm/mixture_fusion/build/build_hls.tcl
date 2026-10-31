# Execute using the HLS command supported by the installed AMD tool version.
if {![info exists ::env(FPGA_PART)] || ![string match "xc7z020*" $::env(FPGA_PART)]} {
    error "Set FPGA_PART to the complete xc7z020 part from the actual board project."
}
set format q32
if {[info exists ::env(FUSION_FORMAT)]} { set format $::env(FUSION_FORMAT) }
if {$format ni {q32 q16}} { error "FUSION_FORMAT must be q32 or q16" }
set root [file dirname [file dirname [file normalize [info script]]]]
set include "-I$root/deploy -I$root/deploy/$format"
cd [file join $root build]
# Recreates only this generated project; save manual edits before running again.
open_project -reset fusion_hls_$format
set_top fusion_q
add_files [file join $root deploy fusion_hls.cpp] -cflags $include
add_files -tb [file join $root sim tb_fusion.cpp] -cflags "$include -I$root/sim/$format"
open_solution -reset solution1
set_part $::env(FPGA_PART)
create_clock -period 10 -name default
csim_design
csynth_design
cosim_design -rtl verilog
export_design -format ip_catalog
exit
