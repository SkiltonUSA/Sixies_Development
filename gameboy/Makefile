ROOT := $(abspath ..)
GAMEBOY_DIR := $(CURDIR)
BUILD_DIR := $(GAMEBOY_DIR)/build
TOOLS_DIR := $(ROOT)/.tools/gameboy
GBDK_HOME ?= $(TOOLS_DIR)/gbdk
LCC := $(GBDK_HOME)/bin/lcc
ROMUSAGE := $(GBDK_HOME)/bin/romusage
PYTHON ?= python3

TARGET := $(BUILD_DIR)/sixies.gb
SOURCES := $(sort $(wildcard src/*.c))
HEADERS := $(sort $(wildcard include/*.h))
LCCFLAGS := -debug -Wm-yS -Wm-yc -Wm-yj -Wm-ynSIXIES \
	-Wm-yt0x1B -Wm-ya1 -Wm-yoA

.PHONY: all setup test ci doctor doctor-desktop run run-mgba music clean

all: $(TARGET)

setup:
	./scripts/setup-tools.sh

$(BUILD_DIR):
	mkdir -p "$@"

$(TARGET): $(SOURCES) $(HEADERS) | $(BUILD_DIR)
	@if [ ! -x "$(LCC)" ]; then ./scripts/setup-tools.sh; fi
	"$(LCC)" $(LCCFLAGS) -Iinclude -o "$@" $(SOURCES)

test: $(TARGET)
	"$(PYTHON)" scripts/verify-rom.py "$(TARGET)"
	"$(ROMUSAGE)" "$(BUILD_DIR)/sixies.noi" -gA

ci: clean all test

doctor:
	./scripts/doctor.sh --core

doctor-desktop: $(TARGET)
	./scripts/doctor.sh

run: $(TARGET)
	./scripts/run-emulator.sh sameboy "$<"

run-mgba: $(TARGET)
	./scripts/run-emulator.sh mgba "$<"

music:
	./scripts/open-music-tracker.sh

clean:
	$(RM) -r "$(BUILD_DIR)"
