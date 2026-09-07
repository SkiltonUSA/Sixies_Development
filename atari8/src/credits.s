; ---------------------------------------------------------------------------
; Native ANTIC-F credits page. Design/studio credits appear first; the centered
; music credit is revealed two seconds later. Text stays native so it remains
; sharp at 320x192.
; ---------------------------------------------------------------------------

.segment "LOGIC"

; Unattended title rotation, matching the other Sixies ports:
; Title (5 seconds) -> Top 10 (5 seconds) -> Credits (11 seconds) -> repeat.
; A start action on any card leaves the rotation; C opens Credits from Title or
; Top 10 and returns from Credits. LOGIC keeps growth independent of the
; bank-safe CODE segment and its following aligned display list.
wait_for_title:
@title:
    lda #0
    sta credits_reveal_frames
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
    lda credits_reveal_frames
    beq @timer
    sec
    sbc zp_temp
    bcc @reveal
    beq @reveal
    sta credits_reveal_frames
    jmp @timer
@reveal:
    ; Drawing uses shared scratch, so preserve the elapsed-frame count.
    lda zp_temp
    pha
    lda #0
    sta credits_reveal_frames
    jsr reveal_music_credit
    pla
    sta zp_temp
@timer:
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
    jsr draw_credits_logo

    lda #0
    sta credits_line_index
@initial_copy:
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
    cpx #CREDITS_INITIAL_COUNT
    bne @initial_copy

    lda #<credits_return
    sta zp_text
    lda #>credits_return
    sta zp_text+1
    lda #176
    ldx #10
    jsr draw_text
    jsr arm_credits_video

    ; The attract controller reveals this later without blocking input.
    lda #120
    sta credits_reveal_frames
    rts

reveal_music_credit:
@music_copy:
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
    bne @music_copy
    rts

CREDITS_INITIAL_COUNT = 2
CREDITS_TEXT_COUNT = 4

credits_text_lo:
    .byte <credits_design, <credits_studio
    .byte <credits_music, <credits_composer
credits_text_hi:
    .byte >credits_design, >credits_studio
    .byte >credits_music, >credits_composer
credits_text_rows:
    .byte 80,92,116,132
credits_text_columns:
    .byte 4,7,10,4

credits_design:         .asciiz "DESIGN, CODE AND ART DSKILTON."
credits_studio:         .asciiz "STUDIO313 GAMES, (C) 2026"
credits_music:          .asciiz "MUSIC, ETERNITY 1 BY"
credits_composer:       .asciiz "PRZEMYSLAW LEWANDOWSKI, SONIX"
credits_return:         .asciiz "PRESS SPACE OR FIRE"

; Draw the reduced 96x24 logo at the top center of the 320-pixel framebuffer
; using the shared byte-aligned monochrome blitter.
draw_credits_logo:
    lda #<credits_logo_asset
    sta zp_asset
    lda #>credits_logo_asset
    sta zp_asset+1
    lda #14
    sta blit_x
    lda #0
    sta blit_y
    lda #12
    sta blit_width
    lda #24
    sta blit_height
    jmp blit_or

.segment "BSS"
credits_line_index: .res 1
attract_seconds:    .res 1
attract_ticks_lo:   .res 1
attract_ticks_hi:   .res 1
attract_last_frame: .res 1
credits_reveal_frames: .res 1
