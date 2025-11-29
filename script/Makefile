# Makefile for BDD-based netlist synthesis and simulation
# Integrates Python synthesis with ModelSim/Questa simulation

# Configuration
SPEC_FILE ?= ../lab3/test_spec.txt
N_INPUTS ?= 3
TESTNAME ?= testbench

# Tool paths (modify if needed)
vlib ?= vlib
vmap ?= vmap
vlog ?= vlog
vsim ?= vsim

# Directories
export WORKAREA := $(shell pwd | sed 's|/script||')
export SRC_DIR := $(WORKAREA)/src
export TB_DIR := $(WORKAREA)/tb
export MODEL_DIR := $(WORKAREA)/model
export SCRIPT_DIR := $(WORKAREA)/script

# Default target
all: clean synthesize build run
	@echo "Simulation complete!"

# Synthesize BDD netlist
synthesize:
	@echo "========================================"
	@echo "Step 1: BDD Synthesis"
	@echo "========================================"
	python3 $(SCRIPT_DIR)/synthesize.py $(SPEC_FILE) $(N_INPUTS)
	@echo ""

# Build simulation
build:
	@echo "========================================"
	@echo "Step 2: Compile Verilog"
	@echo "========================================"
	mkdir -p log
	mkdir -p wave
	$(vlib) work
	$(vmap) work work
	$(vlog) -f compile.f
	@echo ""

# Run simulation
run:
	@echo "========================================"
	@echo "Step 3: Run Simulation"
	@echo "========================================"
	$(vsim) -c -l $(TESTNAME).log -voptargs="+acc" work.$(TESTNAME) -do "log -r /*;run -all; exit"
	@mv $(TESTNAME).log log/ 2>/dev/null || true
	@cp -rf vsim.wlf wave/$(TESTNAME).wlf 2>/dev/null || true
	@ln -sf ./log/$(TESTNAME).log sim.log 2>/dev/null || true
	@echo ""
	@echo "Log file: log/$(TESTNAME).log"
	@echo ""

# Open GUI for waveform viewing
dump: clean synthesize build
	@echo "Opening ModelSim GUI..."
	$(vsim) -gui work.$(TESTNAME)

# View waveform from previous run
view:
	@echo "Opening waveform viewer..."
	$(vsim) -view wave/$(TESTNAME).wlf

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf work
	rm -rf wave
	rm -rf log
	rm -rf *.ini
	rm -rf *.log
	rm -rf *.wlf
	rm -rf transcript
	@echo "Clean complete"
	@echo ""

# Clean everything including generated files
cleanall: clean
	@echo "Cleaning generated files..."
	rm -rf $(SRC_DIR)/netlist.sv
	rm -rf $(MODEL_DIR)/ref_model.v
	rm -rf $(TB_DIR)/testbench.sv
	@echo "Cleanall complete"
	@echo ""

# Show configuration
config:
	@echo "Configuration:"
	@echo "  Spec file:   $(SPEC_FILE)"
	@echo "  Inputs:      $(N_INPUTS)"
	@echo "  Testname:    $(TESTNAME)"
	@echo "  Work area:   $(WORKAREA)"
	@echo ""

# Help
help:
	@echo "BDD Synthesis Simulation Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all        - Clean, synthesize, build, and run (default)"
	@echo "  synthesize - Run BDD synthesis (Python)"
	@echo "  build      - Compile Verilog files"
	@echo "  run        - Run simulation"
	@echo "  dump       - Open ModelSim GUI"
	@echo "  view       - View waveform from previous run"
	@echo "  clean      - Clean build artifacts"
	@echo "  cleanall   - Clean everything including generated files"
	@echo "  config     - Show current configuration"
	@echo "  help       - Show this help"
	@echo ""
	@echo "Variables:"
	@echo "  SPEC_FILE=<file>  - Specification file (default: ../lab3/test_spec.txt)"
	@echo "  N_INPUTS=<n>      - Number of inputs (default: 3)"
	@echo "  TESTNAME=<name>   - Testbench module name (default: testbench)"
	@echo ""
	@echo "Examples:"
	@echo "  make                                    # Full flow with defaults"
	@echo "  make SPEC_FILE=my_spec.txt N_INPUTS=4   # Custom spec"
	@echo "  make build run                          # Skip synthesis"
	@echo "  make dump                               # Open GUI"
	@echo ""

.PHONY: all synthesize build run dump view clean cleanall config help
