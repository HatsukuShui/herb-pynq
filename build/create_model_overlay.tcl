# Run after build_models.tcl has exported small_lr and fusion_q32.
set root [file dirname [file dirname [info script]]]
if {[info exists ::env(PROJECT_ROOT)]} {set root [string map {\\ /} $::env(PROJECT_ROOT)]}
cd $root
set output $root/build/model_overlay
if {[file exists $output]} {error "Project already exists: $output (open its .xpr to continue)."}
set repos {}
foreach model {small_lr fusion_q32} {
    set repo $root/build/models/$model/solution1/impl/ip
    if {![file exists $repo/component.xml]} {error "Missing exported HLS IP: $repo"}
    lappend repos $repo
}
create_project herb_models $output -part xc7z020clg400-1
set_property ip_repo_paths $repos [current_project]
update_ip_catalog
create_bd_design herb_models
set ps7_0 [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:* ps7_0]
source $root/board/pynq_z2_ps.tcl
set_property -dict [list CONFIG.PCW_USE_M_AXI_GP0 {1} CONFIG.PCW_USE_M_AXI_GP1 {0} \
 CONFIG.PCW_USE_S_AXI_GP0 {0} CONFIG.PCW_USE_S_AXI_HP0 {0} CONFIG.PCW_USE_S_AXI_HP2 {0} \
 CONFIG.PCW_USE_FABRIC_INTERRUPT {0} CONFIG.PCW_IRQ_F2P_INTR {0} \
 CONFIG.PCW_GPIO_EMIO_GPIO_ENABLE {0} CONFIG.PCW_EN_CLK1_PORT {0} \
 CONFIG.PCW_EN_CLK2_PORT {0} CONFIG.PCW_EN_CLK3_PORT {0} \
 CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ {100}] $ps7_0
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 -config {make_external "FIXED_IO, DDR" apply_board_preset "0" Master "Disable" Slave "Disable"} $ps7_0
foreach {name top} {small_classifier small_lr_q fusion_classifier fusion_q} {
    set defs [get_ipdefs -all -filter "NAME == $top"]
    if {[llength $defs]!=1} {error "Expected one IP definition for $top, found: $defs"}
    create_bd_cell -type ip -vlnv [get_property VLNV [lindex $defs 0]] $name
    apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Master "/ps7_0/M_AXI_GP0" Clk "/ps7_0/FCLK_CLK0 (100 MHz)"} [get_bd_intf_pins $name/s_axi_CTRL]
}
assign_bd_address
validate_bd_design
save_bd_design
set bd [get_files */herb_models.bd]
generate_target all $bd
set wrapper [make_wrapper -files $bd -top]
add_files $wrapper
set_property top herb_models_wrapper [current_fileset]
update_compile_order -fileset sources_1
write_bd_tcl $root/build/model_overlay/recreate_bd.tcl
puts "MODEL_OVERLAY_CREATED: $output/herb_models.xpr"
close_project
