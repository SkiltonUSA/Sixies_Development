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
INCLUDES := src/hardware.inc src/rules.s src/graphics.s src/sound.s \
	src/sid_music.s src/high_scores.s src/credits.s \
	assets/music/eternity_1_intro_softbass.lz16
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
	$(ATARI_DIR)/assets/title_master.png \
	$(ATARI_DIR)/assets/game_logo_master.png \
	$(ROOT)/apple2/assets/grid_master.png \
	$(ROOT)/apple2/assets/game_grid_dhgr_mono_master.a2fm \
	$(ROOT)/apple2/assets/game_grid_dhgr_mono_reference.png \
	$(ROOT)/apple2/assets/presents_master.ppm \
	$(ROOT)/apple2/assets/game_over_master.png \
	$(ROOT)/apple2/scripts/generate_instructions.py \
	$(ROOT)/apple2/scripts/generate_presents.py \
	$(ROOT)/apple2/scripts/import_a2fm_asset.py \
	$(ROOT)/src/assets/main_mascot.asm \
	$(ROOT)/src/assets/main_mascot_bitmap.bin \
	$(ROOT)/src/assets/main_mascot_screen.bin \
	$(ATARI_DIR)/assets/high_score_mascot_master.png \
	$(ROOT)/src/assets/font/SixiesFont_charset.bin \
	$(ROOT)/src/assets/exclamation_sprites.bin \
	$(ROOT)/src/assets/exclamation_sprites_data.asm \
	$(ROOT)/src/assets/merge_firework_sprite.asm \
	$(wildcard $(ATARI_DIR)/assets/dice/die_*.asm) \
	$(wildcard $(ROOT)/apple2/assets/merge_*_master.png)

MUSIC_SID := $(ROOT)/.context/attachments/jOUZOu/Eternity_1_intro.sid
MUSIC_DIR := $(BUILD_DIR)/music
MUSIC_ASM := $(ATARI_DIR)/src/music/eternity_1_intro.s
MUSIC_SAPR := $(MUSIC_DIR)/eternity_1_intro_softbass.sapr
MUSIC_LZ16 := $(ATARI_DIR)/assets/music/eternity_1_intro_softbass.lz16
SID2SAPR := $(TOOLS_DIR)/saprtools/sid2sapr/sid2sapr
LZSS_SAP := $(TOOLS_DIR)/saprtools/lzss-sap/bin/lzss
DEMO_MUSIC_OBJ := $(BUILD_DIR)/demo_music.o
DEMO_MUSIC_XEX := $(BUILD_DIR)/demo_music.xex
DEMO_HIGH_SCORES_OBJ := $(BUILD_DIR)/demo_high_scores.o
DEMO_HIGH_SCORES_XEX := $(BUILD_DIR)/demo_high_scores.xex
DEMO_HIGH_SCORES_DISK := $(BUILD_DIR)/demo_high_scores.atr

.PHONY: all setup-tools assets test crunch disk run run64 run128 doctor clean \
	music music-sapr demo-music run-demo-music

.PHONY: demo-high-scores demo-high-scores-disk run-demo-high-scores

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

$(DISK): $(CRUNCHED) scripts/package_disk.sh scripts/preserve_high_scores.py
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

# Regenerate the POKEY music stream from the source .sid (needs the attachment
# and py65 in the tools venv).  The generated src/music/eternity_1_intro.s is
# committed, so normal builds do not require this step.
music: | $(BUILD_DIR)
	@if [ ! -f "$(MUSIC_SID)" ]; then \
		echo "source SID not found: $(MUSIC_SID)"; exit 1; fi
	@if [ ! -x "$(VENV_PYTHON)" ]; then ./scripts/setup-tools.sh; fi
	mkdir -p "$(MUSIC_DIR)"
	# --ntsc-sid tunes pitch to NTSC (~+3.8%); --semitones lifts it a little
	# further because the NTSC-only tuning still sounded flat.
	"$(VENV_PYTHON)" scripts/sid_to_pokey.py "$(MUSIC_SID)" \
		--outdir "$(MUSIC_DIR)" --seconds 40 --detect-loop --csv \
		--ntsc-sid --semitones 1.75
	cp "$(MUSIC_DIR)/eternity_1_intro.s" "$(MUSIC_ASM)"
	@echo "Preview WAV: $(MUSIC_DIR)/eternity_1_intro.wav"

# Regenerate the compressed title stream used by the game. sid2sapr produces
# native mono POKEY data; its softbass player supplies the missing low octaves.
music-sapr: | $(BUILD_DIR)
	@if [ ! -f "$(MUSIC_SID)" ]; then \
		echo "source SID not found: $(MUSIC_SID)"; exit 1; fi
	@if [ ! -x "$(SID2SAPR)" ] || [ ! -x "$(LZSS_SAP)" ]; then \
		./scripts/setup-tools.sh; fi
	mkdir -p "$(MUSIC_DIR)" "$(dir $(MUSIC_LZ16))"
	"$(SID2SAPR)" -b softbass -a -p 9 -n 961 \
		-o "$(MUSIC_SAPR)" "$(MUSIC_SID)"
	"$(LZSS_SAP)" -6 "$(MUSIC_SAPR)" "$(MUSIC_LZ16)"
	@echo "Compressed SID2SAPR title stream: $(MUSIC_LZ16)"

# Standalone player .xex that plays the converted tune on POKEY.
$(DEMO_MUSIC_XEX): src/demo_music.s src/sid_music.s $(MUSIC_LZ16) src/hardware.inc $(CONFIG) | $(BUILD_DIR)
	ca65 -g -I . -o "$(DEMO_MUSIC_OBJ)" src/demo_music.s
	ld65 -C "$(CONFIG)" -o "$@" "$(DEMO_MUSIC_OBJ)"

demo-music: $(DEMO_MUSIC_XEX)

run-demo-music: $(DEMO_MUSIC_XEX)
	./scripts/run-emulator.sh "$(DEMO_MUSIC_XEX)" 64

$(DEMO_HIGH_SCORES_XEX): $(SOURCE) $(INCLUDES) $(CONFIG) $(ASSET_STAMP) | $(BUILD_DIR)
	ca65 -g -D HIGH_SCORE_DEMO=1 -I . -o "$(DEMO_HIGH_SCORES_OBJ)" "$(SOURCE)"
	ld65 -C "$(CONFIG)" -o "$@" "$(DEMO_HIGH_SCORES_OBJ)"

demo-high-scores: $(DEMO_HIGH_SCORES_XEX)

$(DEMO_HIGH_SCORES_DISK): $(DEMO_HIGH_SCORES_XEX) scripts/package_disk.sh scripts/preserve_high_scores.py
	./scripts/package_disk.sh "$(DIR2ATR)" "$(DEMO_HIGH_SCORES_XEX)" "$@"

demo-high-scores-disk: $(DEMO_HIGH_SCORES_DISK)

run-demo-high-scores: $(DEMO_HIGH_SCORES_DISK)
	./scripts/run-emulator.sh "$(DEMO_HIGH_SCORES_DISK)" 64

clean:
	rm -rf "$(BUILD_DIR)"
