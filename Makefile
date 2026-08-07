ROOT := $(CURDIR)
LOCAL_ACME := $(ROOT)/.tools/acme/bin/acme
SYSTEM_ACME := $(shell command -v acme 2>/dev/null)
ACME := $(if $(wildcard $(LOCAL_ACME)),$(LOCAL_ACME),$(SYSTEM_ACME))
TARGET := build/dice_merge.prg
SOURCE := src/grid_base.asm
ASSETS := $(wildcard src/assets/*.asm)
BINARY_ASSETS := $(wildcard src/assets/*.bin)
KOALA_SOURCE := src/assets/game_over_koala.kla
KOALA_MASTER := src/assets/game_over_logo_flat_master.png
KOALA_PACKED := src/assets/game_over_koala_packed.bin
KOALA_TABLES := src/assets/game_over_koala_tables.asm
TITLE_MASTER := src/assets/title_logo_flat_master.png
TITLE_BITMAP := src/assets/title_bitmap.bin
TITLE_SCREEN := src/assets/title_screen.bin
TITLE_COLOR := src/assets/title_color.bin
MASCOT_MASTER := src/assets/main_mascot_master.png
MASCOT_BITMAP := src/assets/main_mascot_bitmap.bin
MASCOT_SCREEN := src/assets/main_mascot_screen.bin
FONT_SHEET := src/assets/font/SixiesFont_sheet.png
FONT_SOURCE := src/assets/font/SixiesFont_image.asm
FONT_CHARSET := src/assets/font/SixiesFont_charset.bin
FONT_COLORS := src/assets/font/SixiesFont_colors.asm
FONT_PREVIEW := src/assets/font/SixiesFont_preview.png
FONT_DIGITS16 := src/assets/font/SixiesDigits16.bin
FONT_DIGITS_PREVIEW := src/assets/font/SixiesDigits16_preview.png
FONT_GAME_OVER := src/assets/game_over.asm
FONT_GAME_OVER_PROMPT := src/assets/game_over_prompt.asm
FONT_DIGITS := src/assets/large_digits.asm

.PHONY: all setup-acme run clean

all: $(TARGET)

setup-acme:
	./scripts/setup-acme.sh

build:
	mkdir -p build

$(KOALA_SOURCE): $(KOALA_MASTER) scripts/convert-solid-koala.py
	./scripts/convert-solid-koala.py "$(KOALA_MASTER)" src/assets game_over_koala
	ffmpeg -v error -y -i src/assets/game_over_koala_preview.ppm src/assets/game_over_koala_preview.png

$(KOALA_PACKED): $(KOALA_SOURCE) scripts/pack-koala.py
	./scripts/pack-koala.py "$(KOALA_SOURCE)" src/assets

$(KOALA_TABLES): $(KOALA_PACKED)
	@test -f "$@"

$(TITLE_BITMAP): $(TITLE_MASTER) scripts/convert-solid-koala.py
	./scripts/convert-solid-koala.py "$(TITLE_MASTER)" src/assets title
	ffmpeg -v error -y -i src/assets/title_preview.ppm src/assets/title_preview.png

$(TITLE_SCREEN) $(TITLE_COLOR): $(TITLE_BITMAP)
	@test -f "$@"

$(MASCOT_BITMAP): $(MASCOT_MASTER) scripts/convert-main-mascot.py
	./scripts/convert-main-mascot.py "$(MASCOT_MASTER)" src/assets
	ffmpeg -v error -y -i src/assets/main_mascot_preview.ppm src/assets/main_mascot_preview.png

$(MASCOT_SCREEN): $(MASCOT_BITMAP)
	@test -f "$@"

$(FONT_SOURCE): $(FONT_SHEET) scripts/extract-font-sheet.py
	./scripts/extract-font-sheet.py "$(FONT_SHEET)" src/assets/font
	ffmpeg -v error -y -i src/assets/font/SixiesFont_preview.ppm "$(FONT_PREVIEW)"
	ffmpeg -v error -y -i src/assets/font/SixiesDigits16_preview.ppm "$(FONT_DIGITS_PREVIEW)"

$(FONT_CHARSET) $(FONT_COLORS) $(FONT_PREVIEW) $(FONT_DIGITS16) $(FONT_DIGITS_PREVIEW): $(FONT_SOURCE)
	@test -f "$@"

$(FONT_GAME_OVER): $(FONT_SOURCE) $(FONT_DIGITS16) scripts/build-font-assets.py
	./scripts/build-font-assets.py "$(FONT_SOURCE)" src/assets "$(FONT_DIGITS16)"

$(FONT_DIGITS): $(FONT_GAME_OVER)
	@test -f "$@"

$(FONT_GAME_OVER_PROMPT): $(FONT_GAME_OVER)
	@test -f "$@"

$(TARGET): $(SOURCE) $(ASSETS) $(BINARY_ASSETS) $(KOALA_PACKED) $(KOALA_TABLES) | build
	@if [ ! -x "$(LOCAL_ACME)" ]; then ./scripts/setup-acme.sh; fi
	@"$(LOCAL_ACME)" -f cbm -o "$(TARGET)" "$(SOURCE)"

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
