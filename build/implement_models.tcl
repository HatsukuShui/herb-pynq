set root [file dirname [file dirname [info script]]]
if {[info exists ::env(PROJECT_ROOT)]} {set root [string map {\\ /} $::env(PROJECT_ROOT)]}
open_project $root/build/model_overlay/herb_models.xpr
launch_runs impl_1 -to_step route_design -jobs 4
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation failed"}
open_run impl_1
set out $root/report/model_overlay
file mkdir $out
report_timing_summary -file $out/timing.rpt
report_utilization -file $out/utilization.rpt
report_drc -file $out/drc.rpt
foreach delay {max min} {
    set paths [get_timing_paths -delay_type $delay -max_paths 1]
    if {![llength $paths] || [get_property SLACK [lindex $paths 0]] < 0} {error "Timing check failed ($delay)"}
}
file mkdir $root/build/deploy
close_design
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
if {[get_property STATUS [get_runs impl_1]] ne "write_bitstream Complete!"} {error "Bitstream run failed"}
open_run impl_1
file copy -force $root/build/model_overlay/herb_models.runs/impl_1/herb_models_wrapper.bit $root/build/deploy/herb_models.bit
file mkdir $root/build/deploy/hardware_export
write_hw_platform -fixed -include_bit -force -file $root/build/deploy/hardware_export/herb_models.xsa
set hwh [get_files -all */herb_models.hwh]
if {![llength $hwh]} {set hwh [glob $root/build/model_overlay/herb_models.gen/sources_1/bd/herb_models/hw_handoff/*.hwh]}
file copy -force [lindex $hwh 0] $root/build/deploy/herb_models.hwh
close_project
