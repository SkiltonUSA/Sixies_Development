BasicUpstart2(start)

.const SCREEN   = $0400
.const CHARSET  = $2000

start:
    sei

    // VIC bank 0, screen at $0400, charset at $2000
    lda #$18
    sta $d018

    lda #$00
    sta $d020
    sta $d021

    // Example: display "SIXIES" using character codes
    lda #'S'
    sta SCREEN+0
    lda #'I'
    sta SCREEN+1
    lda #'X'
    sta SCREEN+2
    lda #'I'
    sta SCREEN+3
    lda #'E'
    sta SCREEN+4
    lda #'S'
    sta SCREEN+5

loop:
    jmp loop

* = CHARSET
.import binary "SixiesFont_charset.bin"
