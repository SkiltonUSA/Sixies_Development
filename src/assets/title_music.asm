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

InitTitleMusicImpl:
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

titleMusicNtscDivider: !byte 0
titleMusicActive:      !byte 0

* = $a000
TitleMusicData:
!bin "src/assets/title_music.bin"
