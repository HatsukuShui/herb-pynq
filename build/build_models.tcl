# Vitis 2026.1: vitis-run --mode hls --tcl build/build_models.tcl
set root [file dirname [file dirname [info script]]]
if {[info exists ::env(PROJECT_ROOT)]} {set root [string map {\\ /} $::env(PROJECT_ROOT)]}
set delivery [file join $root third_party algorithm_20261013 shuishengxi_delivery]
set model small_lr
if {[info exists ::env(MODEL)]} {set model $::env(MODEL)}
if {$model ni {small_lr small_mlp fusion_q32 fusion_q16}} {error "Unknown MODEL: $model"}
set output [file join $root build models $model]
if {[file exists $output]} {error "Build exists: $output. Preserve it and choose a fresh output directory."}
open_project $output
if {[string match small_* $model]} {
    set dir [file join $delivery small_herb deploy]
    set top ${model}_q
    set flag -DSMALL_HLS_LR
    if {$model eq "small_mlp"} {set flag -DSMALL_HLS_MLP}
    add_files [file join $dir small_hls.cpp] -cflags "-I$dir"
    add_files -tb [file join $dir tb_small.cpp] -cflags "-I$dir $flag"
} else {
    set dir [file join $delivery mixture_fusion]
    set format [string range $model 7 end]
    set top fusion_q
    set flags "-I$dir/deploy -I$dir/deploy/$format"
    add_files [file join $dir deploy fusion_hls.cpp] -cflags $flags
    add_files -tb [file join $dir sim tb_fusion.cpp] -cflags "$flags -I$dir/sim/$format"
}
set_top $top
open_solution solution1 -flow_target vivado
set_part xc7z020clg400-1
create_clock -period 10 -name default
csim_design
csynth_design
cosim_design -rtl verilog
export_design -format ip_catalog
exit
