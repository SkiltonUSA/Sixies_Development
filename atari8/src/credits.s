; ---------------------------------------------------------------------------
; Native ANTIC-F credits page. The composition follows the supplied mockup:
; a centered heading, decorative dice on the left, compact centered copy, and
; one clear return prompt. Text stays native so it remains sharp at 320x192.
; ---------------------------------------------------------------------------

.segment "AUXCODE"

; Unattended title rotation, matching the other Sixies ports:
; Title (5 seconds) -> Top 10 (5 seconds) -> Credits (11 seconds) -> repeat.
; A start action on any card leaves the rotation; C opens Credits from Title or
; Top 10 and returns from Credits. Keeping this controller in HIRAM avoids
; moving the page-aligned display list in the tight 64K memory map.
wait_for_title:
@title:
    lda #5
    jsr wait_attract_seconds
    bcc @top_scores
    cmp #ACTION_CREDITS
    beq @show_credits
    rts

@top_scores:
    lda #0
    sta high_score_editing
    lda #HIGH_SCORE_COUNT
    jsr show_high_scores
    lda #5
    jsr wait_attract_seconds
    bcc @show_credits
    cmp #ACTION_CREDITS
    beq @show_credits
    rts

@show_credits:
    jsr show_credits
    lda #11
    jsr wait_attract_seconds
    bcc @return_title
    cmp #ACTION_CREDITS
    beq @return_title
    rts

@return_title:
    jsr show_title
    jsr arm_input
    jmp @title

; A=whole seconds. Carry set returns a start/C action in A; carry clear means
; the display interval elapsed. The per-frame loop keeps the SID2SAPR player
; serviced while the attract page remains responsive.
wait_attract_seconds:
    sta attract_seconds
    lda #0
    sta attract_ticks_lo
    sta attract_ticks_hi
@multiply:
    clc
    lda attract_ticks_lo
    adc #60
    sta attract_ticks_lo
    lda attract_ticks_hi
    adc #0
    sta attract_ticks_hi
    dec attract_seconds
    bne @multiply
    lda RTCLOK+2
    sta attract_last_frame
@frame:
    jsr poll_attract_input
    bcs @done
    lda RTCLOK+2
    sta zp_frames
    sec
    sbc attract_last_frame
    beq @frame
    sta zp_temp
    lda zp_frames
    sta attract_last_frame
    sec
    lda attract_ticks_lo
    sbc zp_temp
    sta attract_ticks_lo
    lda attract_ticks_hi
    sbc #0
    sta attract_ticks_hi
    bcc @elapsed
    ora attract_ticks_lo
    beq @elapsed
    lda #0
    sta ATRACT
    jsr sound_update
    jmp @frame
@elapsed:
    clc
@done:
    rts

; Nonblocking title input. Only start controls and C matter in attract mode;
; movement/rotation keys remain ignored until gameplay begins.
poll_attract_input:
    ; Softbass owns POKEY's IRQ vector during this loop, so read the physical
    ; keyboard matrix state directly. SKSTAT bit 2 is low while a key is down.
    lda SKSTAT
    and #$04
    bne @hardware
    lda input_latch
    bne @none
    lda #1
    sta input_latch
    lda KBCODE
    and #KEY_CODE_MASK
    cmp #KEY_C
    beq @credits
    cmp #KEY_SPACE
    beq @start
    cmp #KEY_RETURN
    beq @start
    cmp #KEY_N
    beq @start
    cmp #KEY_Y
    beq @start

@hardware:
    lda CONSOL
    and #1
    beq @pressed
    lda STRIG0
    beq @pressed
    lda STRIG1
    beq @pressed
    lda #0
    sta input_latch
    clc
    rts

@pressed:
    lda input_latch
    bne @none
    lda #1
    sta input_latch
@start:
    lda #ACTION_PLACE
    sec
    rts
@credits:
    lda #ACTION_CREDITS
    sec
    rts
@none:
    clc
    rts

show_credits:
    jsr video_update_begin
    jsr high_score_clear_screen

    lda #<credits_title
    sta zp_text
    lda #>credits_title
    sta zp_text+1
    lda #8
    ldx #16
    jsr draw_text

    lda #28
    jsr set_screen_row
    lda #$FF
    ldy #3
@line:
    sta (zp_screen),y
    iny
    cpy #37
    bne @line

    ; Two supplied die faces echo the mockup's illustrated top-left cluster.
    lda #5
    ldx #3
    jsr draw_sidebar_die
    lda #6
    ldx #7
    jsr draw_sidebar_die

    lda #0
    sta credits_line_index
@copy:
    ldx credits_line_index
    lda credits_text_lo,x
    sta zp_text
    lda credits_text_hi,x
    sta zp_text+1
    lda credits_text_rows,x
    pha
    lda credits_text_columns,x
    tax
    pla
    jsr draw_text
    ldx credits_line_index
    inx
    stx credits_line_index
    cpx #CREDITS_TEXT_COUNT
    bne @copy

    lda #<credits_return
    sta zp_text
    lda #>credits_return
    sta zp_text+1
    lda #176
    ldx #7
    jsr draw_text
    jmp video_update_end

CREDITS_TEXT_COUNT = 10

credits_text_lo:
    .byte <credits_design, <credits_author, <credits_music, <credits_track
    .byte <credits_composer_first, <credits_composer_last, <credits_sonix
    .byte <credits_studio, <credits_games, <credits_year
credits_text_hi:
    .byte >credits_design, >credits_author, >credits_music, >credits_track
    .byte >credits_composer_first, >credits_composer_last, >credits_sonix
    .byte >credits_studio, >credits_games, >credits_year
credits_text_rows:
    .byte 42,54,78,90,102,114,126,144,156,164
credits_text_columns:
    .byte 16,20,21,18,16,16,21,17,22,18

credits_title:          .asciiz "CREDITS"
credits_design:         .asciiz "DESIGN CODE ART"
credits_author:         .asciiz "DSKILTON"
credits_music:          .asciiz "MUSIC"
credits_track:          .asciiz "ETERNITY 1"
credits_composer_first: .asciiz "PRZEMYSLAW"
credits_composer_last:  .asciiz "LEWANDOWSKI"
credits_sonix:          .asciiz "SONIX"
credits_studio:         .asciiz "STUDIO 313 GAMES"
credits_games:          .asciiz "PRESENTS"
credits_year:           .asciiz "COPYRIGHT 2026"
credits_return:         .asciiz "FIRE STARTS  C RETURNS TITLE"

.segment "BSS"
credits_line_index: .res 1
attract_seconds:    .res 1
attract_ticks_lo:   .res 1
attract_ticks_hi:   .res 1
attract_last_frame: .res 1
