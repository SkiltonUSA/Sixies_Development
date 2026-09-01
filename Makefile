ROOT := $(CURDIR)
LOCAL_ACME := $(ROOT)/.tools/acme/bin/acme
SYSTEM_ACME := $(shell command -v acme 2>/dev/null)
ACME = $(if $(wildcard $(LOCAL_ACME)),$(LOCAL_ACME),$(SYSTEM_ACME))
SIDKIT_DIR := $(ROOT)/.tools/c64SIDkit
SIDKIT_PYTHON := $(SIDKIT_DIR)/.venv/bin/python
TARGET := build/dice_merge.prg
CRUNCHED_TARGET := build/dice_merge-crunched.prg
VZ200_DIR := ports/vz200
VZ200_BUILD_DIR := build/vz200
VZ200_SOURCE := $(VZ200_DIR)/asm/sixies.asm
VZ200_BINARY := $(VZ200_BUILD_DIR)/sixies-vz200.bin
VZ200_SNAPSHOT := $(VZ200_BUILD_DIR)/SIXIES.VZ
LOCAL_SJASMPLUS := $(ROOT)/.tools/sjasmplus/bin/sjasmplus
SYSTEM_SJASMPLUS := $(shell command -v sjasmplus 2>/dev/null)
SJASMPLUS = $(if $(wildcard $(LOCAL_SJASMPLUS)),$(LOCAL_SJASMPLUS),$(SYSTEM_SJASMPLUS))
SIXIES_MUSIC_SOURCE := src/music/sixies_rhythmic_grammar.asm
SIXIES_MUSIC_RAW := build/sixies_rhythmic_grammar.bin
SIXIES_MUSIC_SID := build/Sixies_Rhythmic_Grammar.sid
SYSTEM_EXOMIZER := $(shell command -v exomizer 2>/dev/null)
EXOMIZER ?= $(if $(SYSTEM_EXOMIZER),$(SYSTEM_EXOMIZER),/Applications/ALBERT.app/Contents/MacOS/exomizer)
JOYDEV2 ?= 4
SOURCE := src/grid_base.asm
ASM_SOURCES := \
	src/assets/title_screen.asm \
	src/assets/title_koala_tables.asm \
	src/assets/merge_firework_code.asm \
	src/assets/high_scores.asm \
	src/assets/sound_effects.asm \
	src/assets/title_prompt.asm \
	src/assets/score_four_digits.asm \
	src/assets/merge_chain_sounds.asm \
	src/assets/joystick_chord.asm \
	src/assets/credits_mascot.asm \
	src/assets/credits_font.asm \
	src/assets/font/SixiesFont_colors.asm \
	src/assets/presents_screen.asm \
	src/assets/title_music.asm \
	src/assets/merge_diagonal_sweep.asm \
	src/assets/merge_mascot_callout.asm \
	src/assets/merge_callout_data.asm \
	src/assets/bottom_controls.asm \
	src/assets/settings_screen.asm \
	src/assets/settings_art.asm \
	src/assets/main_mascot.asm \
	src/assets/game_over_prompt.asm \
	src/assets/merge_shake.asm \
	src/assets/merge_firework_helpers.asm \
	src/assets/game_over_screen.asm \
	src/assets/game_over_koala_tables.asm \
	src/assets/merge_firework_paths.asm \
	src/assets/marching_ants.asm \
	src/assets/merge_grid_sweep.asm \
	src/assets/merge_firework_sprite.asm \
	src/assets/die_one.asm \
	src/assets/die_two.asm \
	src/assets/die_three.asm \
	src/assets/die_four.asm \
	src/assets/die_five.asm \
	src/assets/die_six.asm \
	src/assets/new_game.asm \
	src/assets/settings.asm \
	src/assets/bottom_labels.asm \
	src/assets/large_digits.asm \
	src/assets/game_over.asm
KOALA_SOURCE := src/assets/game_over_koala.kla
KOALA_MASTER := src/assets/game_over_logo_flat_master.png
KOALA_PACKED := src/assets/game_over_koala_packed.bin
KOALA_TABLES := src/assets/game_over_koala_tables.asm
TITLE_MASTER := src/assets/title_logo_flat_master.png
TITLE_BITMAP := src/assets/title_bitmap.bin
TITLE_SCREEN := src/assets/title_screen.bin
TITLE_COLOR := src/assets/title_color.bin
TITLE_PROMPT_SPRITES := src/assets/title_prompt_sprites.bin
TITLE_KLA := src/assets/title.kla
TITLE_PACKED := src/assets/title_koala_packed.bin
TITLE_TABLES := src/assets/title_koala_tables.asm
TITLE_MUSIC_BIN := src/assets/title_music.bin
MASCOT_MASTER := src/assets/main_mascot_master.png
MASCOT_BITMAP := src/assets/main_mascot_bitmap.bin
MASCOT_SCREEN := src/assets/main_mascot_screen.bin
SETTINGS_DICE_MASTER := src/assets/settings_dice_master.png
SETTINGS_DICE_BITMAP := src/assets/settings_dice_bitmap.bin
SETTINGS_DICE_SCREEN := src/assets/settings_dice_screen.bin
CREDITS_MASCOT_MASTER := src/assets/credits_mascot_master.png
CREDITS_MASCOT_BITMAP := src/assets/credits_mascot_bitmap.bin
CREDITS_MASCOT_SCREEN := src/assets/credits_mascot_screen.bin
CREDITS_LOGO_MASTER := src/assets/credits_logo_master.jpg
CREDITS_LOGO_BITMAP := src/assets/credits_logo_bitmap.bin
CREDITS_LOGO_SCREEN := src/assets/credits_logo_screen.bin
PRESENTS_MASTER := src/assets/Studio313.kla
PRESENTS_BITMAP_PACKED := src/assets/presents_bitmap_packed.bin
PRESENTS_SCREEN_PACKED := src/assets/presents_screen_packed.bin
PRESENTS_COLOR_PACKED := src/assets/presents_color_packed.bin
PRESENTS_BACKGROUND := src/assets/presents_background.bin
FONT_SHEET := src/assets/font/SixiesFont_sheet.png
FONT_SOURCE := src/assets/font/SixiesFont_image.asm
FONT_CHARSET := src/assets/font/SixiesFont_charset.bin
FONT_CHARSET16 := src/assets/font/SixiesFont16.bin
FONT_COLORS := src/assets/font/SixiesFont_colors.asm
FONT_PREVIEW := src/assets/font/SixiesFont_preview.png
FONT_PREVIEW16 := src/assets/font/SixiesFont16_preview.png
FONT_DIGITS16 := src/assets/font/SixiesDigits16.bin
FONT_DIGITS_PREVIEW := src/assets/font/SixiesDigits16_preview.png
FONT_GAME_OVER := src/assets/game_over.asm
FONT_GAME_OVER_PROMPT := src/assets/game_over_prompt.asm
FONT_DIGITS := src/assets/large_digits.asm
MERGE_CALLOUT_PACKED := src/assets/merge_callouts_packed.bin
MERGE_CALLOUT_TABLES := src/assets/merge_callout_data.asm
MERGE_CALLOUT_SOURCES := \
	src/assets/exclamations/AWESOME.png \
	src/assets/exclamations/BOOM.png \
	src/assets/exclamations/DANG.png \
	src/assets/exclamations/FIVES.png \
	src/assets/exclamations/LETS_GO.png \
	src/assets/exclamations/SIXIES.png \
	src/assets/exclamations/WHOA.png \
	src/assets/exclamations/WOW.png \
	src/assets/exclamations/YEAH.png \
	src/assets/exclamations/YES.png
BINARY_ASSETS := \
	$(KOALA_PACKED) \
	$(TITLE_PACKED) \
	$(TITLE_MUSIC_BIN) \
	$(TITLE_PROMPT_SPRITES) \
	$(MASCOT_BITMAP) \
	$(MASCOT_SCREEN) \
	$(SETTINGS_DICE_BITMAP) \
	$(SETTINGS_DICE_SCREEN) \
	$(CREDITS_MASCOT_BITMAP) \
	$(CREDITS_MASCOT_SCREEN) \
	$(CREDITS_LOGO_BITMAP) \
	$(CREDITS_LOGO_SCREEN) \
	$(PRESENTS_BITMAP_PACKED) \
	$(PRESENTS_SCREEN_PACKED) \
	$(PRESENTS_COLOR_PACKED) \
	$(PRESENTS_BACKGROUND) \
	$(FONT_CHARSET) \
	$(FONT_CHARSET16) \
	$(MERGE_CALLOUT_PACKED)

.PHONY: all crunch release music test-porting setup-porting setup-acme setup-sidkit setup-vz200-dev vz200 run-vz200 sidkit run clean FORCE

all: $(TARGET)

crunch release: $(CRUNCHED_TARGET)

music: $(SIXIES_MUSIC_SID)

test-porting:
	python3 tests/porting/validate_vectors.py

setup-porting:
	./scripts/setup-porting-workspace.sh

setup-acme:
	./scripts/setup-acme.sh

setup-sidkit:
	./scripts/setup-c64sidkit.sh

setup-vz200-dev:
	./scripts/setup-vz200-dev.sh

vz200: $(VZ200_SNAPSHOT)

$(VZ200_BUILD_DIR):
	mkdir -p "$@"

$(VZ200_BINARY): $(VZ200_SOURCE) | $(VZ200_BUILD_DIR)
	@if [ ! -x "$(LOCAL_SJASMPLUS)" ]; then ./scripts/setup-vz200-dev.sh; fi
	@"$(SJASMPLUS)" --nologo "$(VZ200_SOURCE)"

$(VZ200_SNAPSHOT): $(VZ200_BINARY) scripts/package-vz200.py | $(VZ200_BUILD_DIR)
	@python3 scripts/package-vz200.py "$(VZ200_BINARY)" "$@" --name SIXIES --load-address 0x7AE9

run-vz200: $(VZ200_SNAPSHOT)
	@bash scripts/run-vz200.sh "$(abspath $(VZ200_SNAPSHOT))"

sidkit: setup-sidkit
	cd "$(SIDKIT_DIR)" && "$(SIDKIT_PYTHON)" tools/sfx_tweaker.py

build:
	mkdir -p build

FORCE:

$(KOALA_SOURCE): $(KOALA_MASTER) scripts/convert-solid-koala.py
	./scripts/convert-solid-koala.py "$(KOALA_MASTER)" src/assets game_over_koala
	ffmpeg -v error -y -i src/assets/game_over_koala_preview.ppm src/assets/game_over_koala_preview.png

$(KOALA_PACKED): $(KOALA_SOURCE) scripts/pack-koala.py
	./scripts/pack-koala.py "$(KOALA_SOURCE)" src/assets

$(KOALA_TABLES): $(KOALA_PACKED)
	@test -f "$@"

$(TITLE_BITMAP): $(TITLE_MASTER) $(FONT_CHARSET) scripts/convert-title.py
	./scripts/convert-title.py "$(TITLE_MASTER)" src/assets
	ffmpeg -v error -y -i src/assets/title_preview.ppm src/assets/title_preview.png

$(TITLE_SCREEN) $(TITLE_COLOR) $(TITLE_PROMPT_SPRITES) $(TITLE_KLA): $(TITLE_BITMAP)
	@test -f "$@"

$(TITLE_PACKED) $(TITLE_TABLES): $(TITLE_KLA) scripts/pack-koala.py
	./scripts/pack-koala.py "$(TITLE_KLA)" src/assets title_koala

$(MASCOT_BITMAP): $(MASCOT_MASTER) scripts/convert-main-mascot.py
	./scripts/convert-main-mascot.py "$(MASCOT_MASTER)" src/assets main_mascot 80 80
	ffmpeg -v error -y -i src/assets/main_mascot_preview.ppm src/assets/main_mascot_preview.png

$(MASCOT_SCREEN): $(MASCOT_BITMAP)
	@test -f "$@"

$(SETTINGS_DICE_BITMAP): $(SETTINGS_DICE_MASTER) scripts/convert-main-mascot.py
	./scripts/convert-main-mascot.py "$(SETTINGS_DICE_MASTER)" src/assets settings_dice 64 56 full-palette
	ffmpeg -v error -y -i src/assets/settings_dice_preview.ppm src/assets/settings_dice_preview.png

$(SETTINGS_DICE_SCREEN): $(SETTINGS_DICE_BITMAP)
	@test -f "$@"

$(CREDITS_MASCOT_BITMAP): $(CREDITS_MASCOT_MASTER) scripts/convert-main-mascot.py
	./scripts/convert-main-mascot.py "$(CREDITS_MASCOT_MASTER)" src/assets credits_mascot 96 128
	ffmpeg -v error -y -i src/assets/credits_mascot_preview.ppm src/assets/credits_mascot_preview.png

$(CREDITS_MASCOT_SCREEN): $(CREDITS_MASCOT_BITMAP)
	@test -f "$@"

$(CREDITS_LOGO_BITMAP): $(CREDITS_LOGO_MASTER) scripts/convert-main-mascot.py
	./scripts/convert-main-mascot.py "$(CREDITS_LOGO_MASTER)" src/assets credits_logo 128 40 solid-logo
	ffmpeg -v error -y -i src/assets/credits_logo_preview.ppm src/assets/credits_logo_preview.png

$(CREDITS_LOGO_SCREEN): $(CREDITS_LOGO_BITMAP)
	@test -f "$@"

$(PRESENTS_BITMAP_PACKED): $(PRESENTS_MASTER) $(FONT_CHARSET) scripts/convert-presents.py
	./scripts/convert-presents.py "$(PRESENTS_MASTER)" "$(FONT_CHARSET)" src/assets
	ffmpeg -v error -y -i src/assets/presents_preview.ppm src/assets/presents_preview.png

$(PRESENTS_SCREEN_PACKED) $(PRESENTS_COLOR_PACKED) $(PRESENTS_BACKGROUND): $(PRESENTS_BITMAP_PACKED)
	@test -f "$@"

$(FONT_SOURCE): $(FONT_SHEET) scripts/extract-font-sheet.py
	./scripts/extract-font-sheet.py "$(FONT_SHEET)" src/assets/font
	ffmpeg -v error -y -i src/assets/font/SixiesFont_preview.ppm "$(FONT_PREVIEW)"
	ffmpeg -v error -y -i src/assets/font/SixiesFont16_preview.ppm "$(FONT_PREVIEW16)"
	ffmpeg -v error -y -i src/assets/font/SixiesDigits16_preview.ppm "$(FONT_DIGITS_PREVIEW)"

$(FONT_CHARSET) $(FONT_CHARSET16) $(FONT_COLORS) $(FONT_PREVIEW) $(FONT_PREVIEW16) $(FONT_DIGITS16) $(FONT_DIGITS_PREVIEW): $(FONT_SOURCE)
	@test -f "$@"

$(FONT_GAME_OVER): $(FONT_SOURCE) $(FONT_DIGITS16) scripts/build-font-assets.py
	./scripts/build-font-assets.py "$(FONT_SOURCE)" src/assets "$(FONT_DIGITS16)"

$(FONT_DIGITS): $(FONT_GAME_OVER)
	@test -f "$@"

$(FONT_GAME_OVER_PROMPT): $(FONT_GAME_OVER)
	@test -f "$@"

$(MERGE_CALLOUT_PACKED): $(MERGE_CALLOUT_SOURCES) scripts/build-merge-callouts.py
	python3 scripts/build-merge-callouts.py src/assets/exclamations src/assets
	ffmpeg -v error -y -i src/assets/merge_callouts_preview.ppm src/assets/merge_callouts_preview.png

$(MERGE_CALLOUT_TABLES): $(MERGE_CALLOUT_PACKED)
	@test -f "$@"

$(SIXIES_MUSIC_RAW): $(SIXIES_MUSIC_SOURCE) | build
	@if [ ! -x "$(LOCAL_ACME)" ]; then ./scripts/setup-acme.sh; fi
	@"$(ACME)" --strict-segments -f plain -o "$@" "$<"

$(SIXIES_MUSIC_SID): $(SIXIES_MUSIC_RAW) scripts/package-psid.py | build
	@python3 scripts/package-psid.py "$<" "$@"

$(TARGET): FORCE $(SOURCE) $(ASM_SOURCES) $(BINARY_ASSETS) $(KOALA_TABLES) $(FONT_COLORS) $(TITLE_TABLES) | build
	@if [ ! -x "$(LOCAL_ACME)" ]; then ./scripts/setup-acme.sh; fi
	@"$(ACME)" --strict-segments -f cbm -o "$(TARGET)" "$(SOURCE)"

$(CRUNCHED_TARGET): $(TARGET) | build
	@if [ ! -x "$(EXOMIZER)" ]; then \
		echo "Exomizer 3.1.2 was not found at $(EXOMIZER)."; \
		exit 1; \
	fi
	@"$(EXOMIZER)" sfx basic -o "$(abspath $@)" "$(abspath $(TARGET))"

run: $(TARGET)
	@if command -v x64sc >/dev/null 2>&1; then \
		x64sc -controlport2device 1 -joydev2 "$(JOYDEV2)" -autostart "$(TARGET)"; \
	elif command -v x64 >/dev/null 2>&1; then \
		x64 -controlport2device 1 -joydev2 "$(JOYDEV2)" -autostart "$(TARGET)"; \
	elif [ -x /Applications/vice-arm64-sdl2-3.9/bin/x64sc ]; then \
		/Applications/vice-arm64-sdl2-3.9/bin/x64sc -controlport2device 1 -joydev2 "$(JOYDEV2)" -autostart "$(TARGET)"; \
	else \
		echo "VICE is not installed. Build succeeded; run $(TARGET) in your preferred C64 emulator."; \
		exit 1; \
	fi

clean:
	rm -rf build
