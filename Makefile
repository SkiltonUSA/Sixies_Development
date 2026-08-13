ROOT := $(CURDIR)
LOCAL_ACME := $(ROOT)/.tools/acme/bin/acme
SYSTEM_ACME := $(shell command -v acme 2>/dev/null)
ACME = $(if $(wildcard $(LOCAL_ACME)),$(LOCAL_ACME),$(SYSTEM_ACME))
SIDKIT_DIR := $(ROOT)/.tools/c64SIDkit
SIDKIT_PYTHON := $(SIDKIT_DIR)/.venv/bin/python
TARGET := build/dice_merge.prg
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
	src/assets/credits_mascot.asm \
	src/assets/credits_font.asm \
	src/assets/font/SixiesFont_colors.asm \
	src/assets/presents_screen.asm \
	src/assets/title_music.asm \
	src/assets/merge_diagonal_sweep.asm \
	src/assets/settings_screen.asm \
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
BINARY_ASSETS := \
	$(KOALA_PACKED) \
	$(TITLE_PACKED) \
	$(TITLE_MUSIC_BIN) \
	$(TITLE_PROMPT_SPRITES) \
	$(MASCOT_BITMAP) \
	$(MASCOT_SCREEN) \
	$(CREDITS_MASCOT_BITMAP) \
	$(CREDITS_MASCOT_SCREEN) \
	$(CREDITS_LOGO_BITMAP) \
	$(CREDITS_LOGO_SCREEN) \
	$(PRESENTS_BITMAP_PACKED) \
	$(PRESENTS_SCREEN_PACKED) \
	$(PRESENTS_COLOR_PACKED) \
	$(PRESENTS_BACKGROUND) \
	$(FONT_CHARSET) \
	$(FONT_CHARSET16)

.PHONY: all setup-acme setup-sidkit sidkit run clean FORCE

all: $(TARGET)

setup-acme:
	./scripts/setup-acme.sh

setup-sidkit:
	./scripts/setup-c64sidkit.sh

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
	./scripts/convert-main-mascot.py "$(MASCOT_MASTER)" src/assets
	ffmpeg -v error -y -i src/assets/main_mascot_preview.ppm src/assets/main_mascot_preview.png

$(MASCOT_SCREEN): $(MASCOT_BITMAP)
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

$(PRESENTS_BITMAP_PACKED): $(PRESENTS_MASTER) $(FONT_CHARSET16) scripts/convert-presents.py
	./scripts/convert-presents.py "$(PRESENTS_MASTER)" "$(FONT_CHARSET16)" src/assets
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

$(TARGET): FORCE $(SOURCE) $(ASM_SOURCES) $(BINARY_ASSETS) $(KOALA_TABLES) $(FONT_COLORS) $(TITLE_TABLES) | build
	@if [ ! -x "$(LOCAL_ACME)" ]; then ./scripts/setup-acme.sh; fi
	@"$(ACME)" --strict-segments -f cbm -o "$(TARGET)" "$(SOURCE)"

run: $(TARGET)
	@if command -v x64sc >/dev/null 2>&1; then \
		x64sc -autostart "$(TARGET)"; \
	elif command -v x64 >/dev/null 2>&1; then \
		x64 -autostart "$(TARGET)"; \
	elif [ -x /Applications/vice-arm64-sdl2-3.9/bin/x64sc ]; then \
		/Applications/vice-arm64-sdl2-3.9/bin/x64sc -autostart "$(TARGET)"; \
	else \
		echo "VICE is not installed. Build succeeded; run $(TARGET) in your preferred C64 emulator."; \
		exit 1; \
	fi

clean:
	rm -rf build
