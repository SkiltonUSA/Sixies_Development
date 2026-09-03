; ---------------------------------------------------------------------------
; demo_music.s -- standalone player for the SID2SAPR softbass conversion of
; "Eternity #1 (intro)". Builds to a bootable .xex for checking the exact game
; player in atari800 (or on real hardware) without the rest of Sixies.
;
;   ca65 -I . -o build/demo_music.o src/demo_music.s
;   ld65 -C cfg/sixies.cfg -o build/demo_music.xex build/demo_music.o
;   atari800 build/demo_music.xex
; ---------------------------------------------------------------------------
.setcpu "6502"
.include "src/hardware.inc"

SAVMSC = $0058          ; OS pointer to the text screen RAM

.segment "CODE"
.export start

start:
    sei
    cld
    ldx #$FF
    txs
    lda #3              ; enable POKEY keyboard/serial clocking
    sta SKCTL
    jsr draw_banner
    jsr sid_music_start
    cli                 ; let the OS stage-1 VBI keep RTCLOK ticking

@loop:
    lda RTCLOK+2
@wait:
    cmp RTCLOK+2        ; wait for the next display frame
    beq @wait
    jsr sid_music_tick
    jmp @loop

; Write a one-line label into the OS text screen (internal char codes).
draw_banner:
    ldy #0
@copy:
    lda banner,y
    beq @done
    sta (SAVMSC),y
    iny
    bne @copy
@done:
    rts

.segment "RODATA"
; "SID->POKEY  ETERNITY #1  SONIX" in screen (internal) codes: ascii-32 for
; the 32..95 range, which covers upper case, digits and these symbols.
banner:
    .byte 51,41,36,0,45,15,48,0     ; "SID -.P" spacing filler
    .byte 48,47,43,37,57,0,0        ; "POKEY"
    .byte 37,52,37,50,46,41,52,57,0,3,1,0,0  ; "ETERNITY #1"
    .byte 51,47,46,41,56            ; "SONIX"
    .byte 0

.include "src/sid_music.s"
