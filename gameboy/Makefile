ROOT := $(abspath ..)
GAMEBOY_DIR := $(CURDIR)
BUILD_DIR := $(GAMEBOY_DIR)/build
TOOLS_DIR := $(ROOT)/.tools/gameboy
GBDK_HOME ?= $(TOOLS_DIR)/gbdk
LCC := $(GBDK_HOME)/bin/lcc
ROMUSAGE := $(GBDK_HOME)/bin/romusage
SDAR := $(GBDK_HOME)/bin/sdar
RGBASM := $(TOOLS_DIR)/rgbds-driver/rgbasm
PYTHON ?= python3
HOST_CC ?= cc
ASSET_PYTHON := $(TOOLS_DIR)/venv/bin/python
DEBUG_CHEATS ?= 0
TITLE_MUSIC ?= 0

TARGET := $(BUILD_DIR)/sixies.gb
VERSION_COUNTER := $(GAMEBOY_DIR)/VERSION
VERSION_HEADER := $(GAMEBOY_DIR)/include/build_version.h
SOURCES := $(filter-out src/generated_title_music.c,$(sort $(wildcard src/*.c)))
HEADERS := $(sort $(wildcard include/*.h))
HUGE_DRIVER_DIR := $(GAMEBOY_DIR)/vendor/hUGEDriver
HUGE_DRIVER_OBJ := $(BUILD_DIR)/hUGEDriver.obj
HUGE_DRIVER_SDC_OBJ := $(BUILD_DIR)/hUGEDriver.o
HUGE_DRIVER_LIB := $(BUILD_DIR)/hUGEDriver.lib
LCCFLAGS := -debug -Wm-yS -Wm-yc -Wm-yj -Wm-ynSIXIES \
	-Wm-yt0x1B -Wm-ya1 -Wm-yoA

ifeq ($(DEBUG_CHEATS),1)
LCCFLAGS += -DSIXIES_ENABLE_CHEAT
endif

ifeq ($(TITLE_MUSIC),1)
SOURCES += src/generated_title_music.c
LCCFLAGS += -DSIXIES_ENABLE_TITLE_MUSIC
endif

.PHONY: all assets setup setup-assets build-version test test-emulator ci doctor doctor-desktop run run-mgba music clean

all: $(TARGET)

assets:
	"$(ASSET_PYTHON)" scripts/generate-assets.py

setup-assets:
	"$(PYTHON)" -m venv "$(TOOLS_DIR)/venv"
	"$(ASSET_PYTHON)" -m pip install -r scripts/requirements.txt

setup:
	./scripts/setup-tools.sh
	$(MAKE) setup-assets

build-version:
	"$(PYTHON)" scripts/next-build-version.py --counter "$(VERSION_COUNTER)" --header "$(VERSION_HEADER)"

$(BUILD_DIR):
	mkdir -p "$@"

$(HUGE_DRIVER_OBJ): $(HUGE_DRIVER_DIR)/hUGEDriver.asm $(HUGE_DRIVER_DIR)/include/hUGE.inc $(HUGE_DRIVER_DIR)/include/hUGE_note_table.inc $(HUGE_DRIVER_DIR)/include/hardware.inc | $(BUILD_DIR)
	"$(RGBASM)" -DGBDK -I"$(HUGE_DRIVER_DIR)" -o"$@" "$<"

$(HUGE_DRIVER_SDC_OBJ): $(HUGE_DRIVER_OBJ) $(HUGE_DRIVER_DIR)/tools/rgb2sdas.py | $(BUILD_DIR)
	"$(PYTHON)" "$(HUGE_DRIVER_DIR)/tools/rgb2sdas.py" -b 0 -o "$@" "$<"

$(HUGE_DRIVER_LIB): $(HUGE_DRIVER_SDC_OBJ) | $(BUILD_DIR)
	"$(SDAR)" -ru "$@" "$<"

$(TARGET): build-version $(SOURCES) $(HEADERS) $(HUGE_DRIVER_LIB) | $(BUILD_DIR)
	@if [ ! -x "$(LCC)" ]; then ./scripts/setup-tools.sh; fi
	"$(LCC)" $(LCCFLAGS) -Iinclude -I"$(HUGE_DRIVER_DIR)/include" -Wl-l"$(HUGE_DRIVER_LIB)" -o "$@" $(SOURCES)
	"$(PYTHON)" scripts/archive-versioned-rom.py --counter "$(VERSION_COUNTER)" --rom "$@"

test: $(TARGET)
	"$(ASSET_PYTHON)" tests/dice_shading_test.py
	"$(ASSET_PYTHON)" tests/reference_dice_test.py
	"$(ASSET_PYTHON)" tests/callout_box_test.py
	"$(ASSET_PYTHON)" tests/chain_stars_test.py
	"$(HOST_CC)" -std=c99 -Wall -Wextra -Werror -Iinclude tests/game_rules_test.c src/game.c -o "$(BUILD_DIR)/game-rules-test"
	"$(BUILD_DIR)/game-rules-test"
	"$(HOST_CC)" -std=c99 -Wall -Wextra -Werror -Iinclude tests/scores_test.c src/scores.c -o "$(BUILD_DIR)/scores-test"
	"$(BUILD_DIR)/scores-test"
	"$(PYTHON)" scripts/verify-rom.py "$(TARGET)"
	"$(ROMUSAGE)" "$(BUILD_DIR)/sixies.noi" -gA

ci: clean all test

test-emulator:
	$(MAKE) DEBUG_CHEATS=1 TITLE_MUSIC=1 $(TARGET)
	"$(ASSET_PYTHON)" tests/emulator_smoke.py

doctor:
	./scripts/doctor.sh --core

doctor-desktop: $(TARGET)
	./scripts/doctor.sh

run:
	$(MAKE) DEBUG_CHEATS=1 TITLE_MUSIC=1 $(TARGET)
	./scripts/run-emulator.sh sameboy "$(TARGET)"

run-mgba:
	$(MAKE) DEBUG_CHEATS=1 TITLE_MUSIC=1 $(TARGET)
	./scripts/run-emulator.sh mgba "$(TARGET)"

music:
	./scripts/open-music-tracker.sh

clean:
	$(RM) "$(TARGET)" $(addprefix $(BUILD_DIR)/sixies.,cdb map noi sym) "$(BUILD_DIR)/hUGEDriver.obj" "$(BUILD_DIR)/hUGEDriver.o" "$(BUILD_DIR)/hUGEDriver.lib" "$(BUILD_DIR)/game-rules-test" "$(BUILD_DIR)/scores-test"
