; "Eternity #1 (intro)" by Przemyslaw Lewandowski (Sonix), 1995
; Undying/Sun Designs. Relocated from $1000 to $a000 with sidreloc 1.0.
* = $9700

InitTitleRasterIRQ:
    lda #<TitleMusicRasterIRQ
    sta IRQ_VECTOR
    lda #>TitleMusicRasterIRQ
    sta IRQ_VECTOR + 1
    lda #250
    sta RASTER_LINE
    lda #1
    sta VIC_IRQ_STATUS
    sta VIC_IRQ_ENABLE
    rts

StopTitleRasterIRQ:
    sei
    lda #0
    sta VIC_IRQ_ENABLE
    lda #1
    sta VIC_IRQ_STATUS
    rts

TitleMusicRasterIRQ:
    lda VIC_IRQ_STATUS
    and #1
    beq TitleMusicRasterIRQ_Exit
    lda #1
    sta VIC_IRQ_STATUS
    jsr UpdateTitleMusic
TitleMusicRasterIRQ_Exit:
    jmp IRQ_EXIT

InitTitleMusic:
    jsr ResetSoundEffects
    lda #0
    sta titleMusicNtscDivider
    tax
    tay
    jsr TITLE_MUSIC_INIT
    lda #1
    sta titleMusicActive
    rts

UpdateTitleMusic:
    lda titleMusicActive
    beq UpdateTitleMusic_Done
    lda TV_STANDARD
    bne UpdateTitleMusic_Play
    ; The tune is PAL. Skip every sixth NTSC frame to retain a 50 Hz call rate.
    inc titleMusicNtscDivider
    lda titleMusicNtscDivider
    cmp #6
    bne UpdateTitleMusic_Play
    lda #0
    sta titleMusicNtscDivider
    rts
UpdateTitleMusic_Play:
    jsr TITLE_MUSIC_PLAY
UpdateTitleMusic_Done:
    rts

StopTitleMusic:
    lda #0
    sta titleMusicActive
    ldx #24
StopTitleMusic_ClearSid:
    sta $d400,x
    dex
    bpl StopTitleMusic_ClearSid
    rts

UpdateHighScoreEntryFlash:
    lda frameCounter
    and #8
    beq UpdateHighScoreEntryFlash_Yellow
    lda #COLOR_WHITE
    bne UpdateHighScoreEntryFlash_ColorReady
UpdateHighScoreEntryFlash_Yellow:
    lda #COLOR_YELLOW
UpdateHighScoreEntryFlash_ColorReady:
    cmp highScoreFlashColor
    beq UpdateHighScoreEntryFlash_Done
    sta highScoreFlashColor
    pha
    lda ScreenRowLo + 8
    sta PTR_LO
    lda ScreenRowHi + 8
    sta PTR_HI
    pla
    asl
    asl
    asl
    asl
    ldy #6
UpdateHighScoreEntryFlash_Cell:
    sta (PTR_LO),y
    iny
    cpy #34
    bne UpdateHighScoreEntryFlash_Cell
    lda PTR_LO
    clc
    adc #40
    sta PTR_LO
    bcc UpdateHighScoreEntryFlash_BottomReady
    inc PTR_HI
UpdateHighScoreEntryFlash_BottomReady:
    lda highScoreFlashColor
    asl
    asl
    asl
    asl
    ldy #6
UpdateHighScoreEntryFlash_BottomCell:
    sta (PTR_LO),y
    iny
    cpy #34
    bne UpdateHighScoreEntryFlash_BottomCell
UpdateHighScoreEntryFlash_Done:
    rts

titleMusicNtscDivider: !byte 0
titleMusicActive:      !byte 0
highScoreFlashColor:   !byte $ff

* = $a000
TitleMusicData:
!bin "src/assets/title_music.bin"
