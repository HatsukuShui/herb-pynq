# Finish bitstream/XSA export from the already timing-checked routed design.
set root [file dirname [file dirname [info script]]]
if {[info exists ::env(PROJECT_ROOT)]} {set root [string map {\\ /} $::env(PROJECT_ROOT)]}
open_project $root/build/model_overlay/herb_models.xpr
open_run impl_1
foreach delay {max min} {
    set paths [get_timing_paths -delay_type $delay -max_paths 1]
    if {![llength $paths] || [get_property SLACK [lindex $paths 0]] < 0} {error "Timing check failed ($delay)"}
}
close_design
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
if {[get_property STATUS [get_runs impl_1]] ne "write_bitstream Complete!"} {error "Bitstream run failed"}
open_run impl_1
file mkdir $root/build/deploy
file copy -force $root/build/model_overlay/herb_models.runs/impl_1/herb_models_wrapper.bit $root/build/deploy/herb_models.bit
file mkdir $root/build/deploy/hardware_export
write_hw_platform -fixed -include_bit -force -file $root/build/deploy/hardware_export/herb_models.xsa
file copy -force $root/build/model_overlay/herb_models.gen/sources_1/bd/herb_models/hw_handoff/herb_models.hwh $root/build/deploy/herb_models.hwh
close_project
