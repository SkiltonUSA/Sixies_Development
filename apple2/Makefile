ROOT := $(abspath ..)
APPLE2_DIR := $(CURDIR)
BUILD_DIR := $(APPLE2_DIR)/build
PREVIEW_DIR := $(BUILD_DIR)/previews
ASSET_DIR := $(BUILD_DIR)/assets
GENERATED_DIR := $(BUILD_DIR)/generated
TOOLS_DIR := $(ROOT)/.tools
APPLE2_VENV := $(TOOLS_DIR)/apple2-venv
PYTHON := $(APPLE2_VENV)/bin/python
CC65 := $(shell command -v cl65 2>/dev/null)
APPLECOMMANDER_JAR := $(firstword $(wildcard $(TOOLS_DIR)/applecommander/AppleCommander-ac-*.jar))
IZAPPLE2 := $(TOOLS_DIR)/izapple2/izapple2

TARGET := $(BUILD_DIR)/SIXIES
DISK := $(BUILD_DIR)/sixies.po
MAP := $(BUILD_DIR)/sixies.map
SRC := $(APPLE2_DIR)/src/main.c
ASM_SRC := $(APPLE2_DIR)/src/auxmem.s

TITLE_MASTER := $(APPLE2_DIR)/assets/title_dhgr_mono_master.a2fm
TITLE_REFERENCE := $(APPLE2_DIR)/assets/title_dhgr_mono_reference.png
GAME_OVER_MASTER := $(ROOT)/src/assets/game_over_logo_flat_master.png
GRID_MASTER := $(APPLE2_DIR)/assets/game_grid_dhgr_mono_master.a2fm
GRID_REFERENCE := $(APPLE2_DIR)/assets/game_grid_dhgr_mono_reference.png
MASCOT_MASTER := $(ROOT)/src/assets/main_mascot_master.png
DIE_ONE_MASTER := $(APPLE2_DIR)/assets/die_1_master.png
DIE_TWO_MASTER := $(APPLE2_DIR)/assets/die_2_master.png
DIE_THREE_MASTER := $(APPLE2_DIR)/assets/die_3_master.png
DIE_FOUR_MASTER := $(APPLE2_DIR)/assets/die_4_master.png
DIE_FIVE_MASTER := $(APPLE2_DIR)/assets/die_5_master.png
DIE_SIX_MASTER := $(APPLE2_DIR)/assets/die_6_master.png
MERGE_AWESOME_MASTER := $(APPLE2_DIR)/assets/merge_awesome_master.png
MERGE_BOOM_MASTER := $(APPLE2_DIR)/assets/merge_boom_master.png
MERGE_DANG_MASTER := $(APPLE2_DIR)/assets/merge_dang_master.png
MERGE_FIVES_MASTER := $(APPLE2_DIR)/assets/merge_fives_master.png
MERGE_LETS_GO_MASTER := $(APPLE2_DIR)/assets/merge_lets_go_master.png
MERGE_SIXIES_MASTER := $(APPLE2_DIR)/assets/merge_sixies_master.png
MERGE_WHOA_MASTER := $(APPLE2_DIR)/assets/merge_whoa_master.png
MERGE_YEAH_MASTER := $(APPLE2_DIR)/assets/merge_yeah_master.png
MERGE_WOW_MASTER := $(APPLE2_DIR)/assets/merge_wow_master.png
MERGE_YES_MASTER := $(APPLE2_DIR)/assets/merge_yes_master.png
MERGE_MASTERS := $(MERGE_AWESOME_MASTER) $(MERGE_BOOM_MASTER) $(MERGE_DANG_MASTER) $(MERGE_FIVES_MASTER) $(MERGE_LETS_GO_MASTER) $(MERGE_SIXIES_MASTER) $(MERGE_WHOA_MASTER) $(MERGE_YEAH_MASTER) $(MERGE_WOW_MASTER) $(MERGE_YES_MASTER)

TITLE_MAIN := $(ASSET_DIR)/TITLE.MAIN
TITLE_AUX := $(ASSET_DIR)/TITLE.AUX
GAME_OVER_MAIN := $(ASSET_DIR)/GAMEOVER.MAIN
GAME_OVER_AUX := $(ASSET_DIR)/GAMEOVER.AUX
GRID_A2FM := $(ASSET_DIR)/GRID.A2FM
TITLE_STAMP := $(ASSET_DIR)/title.stamp
GAME_OVER_STAMP := $(ASSET_DIR)/game_over.stamp
GRID_STAMP := $(ASSET_DIR)/grid.stamp
DICE_STAMP := $(ASSET_DIR)/dice.stamp
DICE_HEADER := $(GENERATED_DIR)/dice_assets.h
DICE_BLITS := $(ASSET_DIR)/DICE.BLITS
MERGE_EFFECT_STAMP := $(ASSET_DIR)/merge_effects.stamp
MERGE_EFFECT_HEADER := $(GENERATED_DIR)/merge_effects.h
MERGE_EFFECT_FILES := $(addprefix $(ASSET_DIR)/,MERGESTAR FX00 FX01 FX02 FX03 FX04 FX05 FX06 FX07 FX08 FX09)

.PHONY: all setup-tools assets test disk run debug emulator-check doctor clean

all: $(TARGET)

setup-tools:
	./scripts/setup-tools.sh

$(BUILD_DIR) $(PREVIEW_DIR) $(ASSET_DIR) $(GENERATED_DIR):
	mkdir -p "$@"

$(TITLE_STAMP): $(TITLE_MASTER) $(TITLE_REFERENCE) scripts/import_a2fm_asset.py | $(ASSET_DIR) $(PREVIEW_DIR)
	@if [ ! -x "$(PYTHON)" ]; then ./scripts/setup-tools.sh; fi
	"$(PYTHON)" scripts/import_a2fm_asset.py \
		--input "$(TITLE_MASTER)" \
		--main "$(TITLE_MAIN)" \
		--aux "$(TITLE_AUX)" \
		--preview "$(PREVIEW_DIR)/title_logo.png" \
		--reference "$(TITLE_REFERENCE)"
	touch "$@"

$(GAME_OVER_STAMP): $(GAME_OVER_MASTER) scripts/convert_dhgr_asset.py | $(ASSET_DIR) $(PREVIEW_DIR)
	@if [ ! -x "$(PYTHON)" ]; then ./scripts/setup-tools.sh; fi
	"$(PYTHON)" scripts/convert_dhgr_asset.py \
		--input "$(GAME_OVER_MASTER)" \
		--main "$(GAME_OVER_MAIN)" \
		--aux "$(GAME_OVER_AUX)" \
		--preview "$(PREVIEW_DIR)/game_over_logo.png" \
		--height 160
	touch "$@"

$(GRID_STAMP): $(GRID_MASTER) $(GRID_REFERENCE) $(MASCOT_MASTER) scripts/import_a2fm_grid.py scripts/import_a2fm_asset.py | $(ASSET_DIR) $(PREVIEW_DIR)
	@if [ ! -x "$(PYTHON)" ]; then ./scripts/setup-tools.sh; fi
	"$(PYTHON)" scripts/import_a2fm_grid.py \
		--input "$(GRID_MASTER)" \
		--reference "$(GRID_REFERENCE)" \
		--mascot "$(MASCOT_MASTER)" \
		--output "$(GRID_A2FM)" \
		--preview "$(PREVIEW_DIR)/grid_dhgr.png"
	touch "$@"

$(DICE_STAMP): $(DIE_ONE_MASTER) $(DIE_TWO_MASTER) $(DIE_THREE_MASTER) $(DIE_FOUR_MASTER) $(DIE_FIVE_MASTER) $(DIE_SIX_MASTER) $(GRID_MASTER) scripts/generate_hgr_dice.py | $(ASSET_DIR) $(PREVIEW_DIR) $(GENERATED_DIR)
	@if [ ! -x "$(PYTHON)" ]; then ./scripts/setup-tools.sh; fi
	"$(PYTHON)" scripts/generate_hgr_dice.py \
		--one "$(DIE_ONE_MASTER)" \
		--two "$(DIE_TWO_MASTER)" \
		--three "$(DIE_THREE_MASTER)" \
		--four "$(DIE_FOUR_MASTER)" \
		--five "$(DIE_FIVE_MASTER)" \
		--six "$(DIE_SIX_MASTER)" \
		--grid "$(GRID_MASTER)" \
		--header "$(DICE_HEADER)" \
		--blits "$(DICE_BLITS)" \
		--preview "$(PREVIEW_DIR)/dice_1_6.png"
	touch "$@"

$(MERGE_EFFECT_STAMP): $(MERGE_MASTERS) scripts/generate_merge_effects.py | $(ASSET_DIR) $(PREVIEW_DIR) $(GENERATED_DIR)
	@if [ ! -x "$(PYTHON)" ]; then ./scripts/setup-tools.sh; fi
	"$(PYTHON)" scripts/generate_merge_effects.py \
		--awesome "$(MERGE_AWESOME_MASTER)" \
		--boom "$(MERGE_BOOM_MASTER)" \
		--dang "$(MERGE_DANG_MASTER)" \
		--fives "$(MERGE_FIVES_MASTER)" \
		--lets-go "$(MERGE_LETS_GO_MASTER)" \
		--sixies "$(MERGE_SIXIES_MASTER)" \
		--whoa "$(MERGE_WHOA_MASTER)" \
		--yeah "$(MERGE_YEAH_MASTER)" \
		--wow "$(MERGE_WOW_MASTER)" \
		--yes "$(MERGE_YES_MASTER)" \
		--output-dir "$(ASSET_DIR)" \
		--preview-dir "$(PREVIEW_DIR)" \
		--header "$(MERGE_EFFECT_HEADER)"
	touch "$@"

assets: $(TITLE_STAMP) $(GAME_OVER_STAMP) $(GRID_STAMP) $(DICE_STAMP) $(MERGE_EFFECT_STAMP)

test: setup-tools
	"$(PYTHON)" -m unittest discover -s tests -p 'test_*.py'

$(TARGET): Makefile $(SRC) $(ASM_SRC) $(DICE_STAMP) $(MERGE_EFFECT_STAMP) | $(BUILD_DIR)
	@if [ -z "$(CC65)" ]; then echo "cl65 was not found on PATH."; exit 1; fi
	cl65 -t apple2 -Oirs --codesize 500 --start-addr 0x4000 -I "$(GENERATED_DIR)" \
		-Wl "-D__HIMEM__=0xBF00,-D__STACKSIZE__=0x0300" \
		-m "$(MAP)" \
		-o "$@" \
		"$(SRC)" "$(ASM_SRC)"
	rm -f "$(APPLE2_DIR)/src/main.o" "$(APPLE2_DIR)/src/auxmem.o"

disk: $(DISK)

$(DISK): $(TARGET) assets setup-tools | $(BUILD_DIR)
	@if [ -z "$(APPLECOMMANDER_JAR)" ]; then echo "AppleCommander jar not found under $(TOOLS_DIR)/applecommander"; exit 1; fi
	./scripts/package_disk.sh "$(TARGET)" "$@" "$(ASSET_DIR)"

run: $(DISK) setup-tools
	./scripts/run-emulator.sh "$(DISK)"

debug: $(DISK) setup-tools
	./scripts/run-emulator.sh "$(DISK)" trace

emulator-check: setup-tools
	"$(IZAPPLE2)" -model=2enh -s2=empty -s3=empty -s4=empty -showConfig

doctor: $(DISK) emulator-check
	@echo "Apple II development environment is ready."
	@echo "  compiler: $$(cl65 --version 2>&1 | head -n 1)"
	@echo "  disk image: $(DISK)"
	@echo "  run: make -C apple2 run"
	@echo "  debug: make -C apple2 debug"

clean:
	rm -rf "$(BUILD_DIR)"
	rm -f "$(APPLE2_DIR)/src/main.o" "$(APPLE2_DIR)/src/auxmem.o"
