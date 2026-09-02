ROOT := $(abspath ..)
ATARI_DIR := $(CURDIR)
BUILD_DIR := $(ATARI_DIR)/build
ASSET_DIR := $(BUILD_DIR)/assets
PREVIEW_DIR := $(BUILD_DIR)/previews
TOOLS_DIR := $(ROOT)/.tools/atari8
VENV_PYTHON := $(TOOLS_DIR)/venv/bin/python
DIR2ATR := $(TOOLS_DIR)/bin/dir2atr
ATARICOM := $(TOOLS_DIR)/bin/ataricom

SOURCE := src/main.s
INCLUDES := src/hardware.inc src/rules.s src/graphics.s src/sound.s
CONFIG := cfg/sixies.cfg
OBJECT := $(BUILD_DIR)/sixies.o
TARGET := $(BUILD_DIR)/sixies.xex
CRUNCHED := $(BUILD_DIR)/sixies-crunched.xex
DISK := $(BUILD_DIR)/sixies.atr
MAP := $(BUILD_DIR)/sixies.map
LABELS := $(BUILD_DIR)/sixies.lbl
LISTING := $(BUILD_DIR)/sixies.lst
ASSET_STAMP := $(ASSET_DIR)/.stamp

ASSET_SOURCES := \
	$(ROOT)/apple2/assets/title_dhgr_mono_master.a2fm \
	$(ROOT)/apple2/assets/title_dhgr_mono_reference.png \
	$(ROOT)/apple2/assets/presents_master.ppm \
	$(ROOT)/apple2/assets/game_over_master.png \
	$(ROOT)/apple2/scripts/generate_instructions.py \
	$(ROOT)/apple2/scripts/generate_presents.py \
	$(ROOT)/apple2/scripts/import_a2fm_asset.py \
	$(ROOT)/src/assets/main_mascot.asm \
	$(ROOT)/src/assets/main_mascot_bitmap.bin \
	$(ROOT)/src/assets/main_mascot_screen.bin \
	$(ROOT)/src/assets/main_mascot_master.png \
	$(ROOT)/src/assets/font/SixiesFont_charset.bin \
	$(ROOT)/src/assets/exclamation_sprites.bin \
	$(ROOT)/src/assets/exclamation_sprites_data.asm \
	$(ROOT)/src/assets/merge_firework_sprite.asm \
	$(wildcard $(ATARI_DIR)/assets/dice/die_*.asm) \
	$(wildcard $(ROOT)/apple2/assets/merge_*_master.png)

.PHONY: all setup-tools assets test crunch disk run run64 run128 doctor clean

all: $(TARGET)

setup-tools:
	./scripts/setup-tools.sh

$(BUILD_DIR) $(ASSET_DIR) $(PREVIEW_DIR):
	mkdir -p "$@"

$(ASSET_STAMP): scripts/generate_assets.py $(ASSET_SOURCES) | $(ASSET_DIR) $(PREVIEW_DIR)
	@if [ ! -x "$(VENV_PYTHON)" ]; then ./scripts/setup-tools.sh; fi
	"$(VENV_PYTHON)" scripts/generate_assets.py --output "$(ASSET_DIR)" --previews "$(PREVIEW_DIR)"
	touch "$@"

assets: $(ASSET_STAMP)

$(OBJECT): $(SOURCE) $(INCLUDES) $(CONFIG) $(ASSET_STAMP) | $(BUILD_DIR)
	ca65 -g -I . -l "$(LISTING)" -o "$@" "$<"

$(TARGET): $(OBJECT) $(CONFIG)
	ld65 -C "$(CONFIG)" -m "$(MAP)" -Ln "$(LABELS)" -o "$@" "$<"

$(CRUNCHED): $(TARGET)
	exomizer sfx 8192 -t168 -n -o "$@" "$<"

crunch: $(CRUNCHED)

$(DISK): $(CRUNCHED) scripts/package_disk.sh
	@if [ ! -x "$(DIR2ATR)" ]; then ./scripts/setup-tools.sh; fi
	./scripts/package_disk.sh "$(DIR2ATR)" "$(CRUNCHED)" "$@"

disk: $(DISK)

test: $(TARGET)
	@if [ ! -x "$(VENV_PYTHON)" ]; then ./scripts/setup-tools.sh; fi
	"$(VENV_PYTHON)" -m unittest discover -s tests -p 'test_*.py'

run run64: $(DISK)
	./scripts/run-emulator.sh "$(DISK)" 64

run128: $(DISK)
	./scripts/run-emulator.sh "$(DISK)" 128

doctor: $(DISK) test
	"$(ATARICOM)" "$(TARGET)"
	"$(DIR2ATR)" --help >/dev/null 2>&1 || true
	@echo "Atari 8-bit environment is ready."
	@echo "  64K XEX: $(TARGET)"
	@echo "  crunched: $(CRUNCHED)"
	@echo "  boot ATR: $(DISK)"
	@echo "  64K run:  make -C atari8 run64"
	@echo "  128K run: make -C atari8 run128"

clean:
	rm -rf "$(BUILD_DIR)"
