; Presentation boundary: rules have already committed this group to board.
; Inputs: active_index, group_value/count/queue, merge_depth, current score.
; Preserves board, active_index, placed_second, group_value, merge_depth.
; Clobbers A/X/Y, renderer scratch, group_queue/count and RNG (callout choice).
; Frame waits service input/audio without re-entering renderer or rules. Only
; the latest movement is retained; placement cannot cross the resolution lock.
CHAIN_BANNER_FRAMES = 60

.segment "BSS"
merge_score_string: .res 7       ; six visible cells plus terminator
chain_badge_string: .res 3       ; digit, X, terminator
chain_badge_x:      .res 1
chain_badge_y:      .res 1
chain_badge_dx:     .res 1
chain_badge_step:   .res 1
chain_banner_frames:.res 1
chain_banner_last:  .res 1

.segment "LOGIC"
present_merge:
    jsr redraw_group_cells
    jsr redraw_score_digits
    lda group_value
    jsr play_merge_sound
    lda group_value
    cmp #4
    bcc :+
    jsr run_merge_grid_shake
    lda group_value
:
    cmp #6
    bne :+
    jsr flash_six_clear
:
    jsr run_merge_grid_ripple
    jsr run_merge_star_firework

@merge_value:
    ; Always show the actual award, even with reduced flashing enabled.
    jsr show_merge_score
    lda #18
    jsr wait_frames
    jsr hide_callout
    lda merge_depth
    cmp #2
    bcc @word
    jsr show_chain_reaction_sidebar
    jsr shoot_chain_multiplier

    ; Match the Apple IIe outcomes for every group size: consuming 4s creates
    ; a five, consuming 5s creates a six, and Awesome is reserved for later
    ; generic merges in the same placement turn.
@word:
    lda group_value
    cmp #4
    beq @fives
    cmp #5
    beq @sixies
    lda merge_depth
    cmp #2
    bcs @awesome
    ldx #7
    jsr random_mod_x
    tax
    lda first_merge_callouts,x
    jmp @show
@fives:
    lda #3
    bne @show
@sixies:
    lda #5
    bne @show
@awesome:
    lda #0
@show:
    sta text_index
    jsr show_callout
    lda #CALLOUT_FRAMES
    jsr wait_frames
    jsr hide_callout
    lda merge_depth
    cmp #2
    bcc :+
    jmp arm_chain_reaction_sidebar
:
    rts

; Leave the sidebar banner active for one additional second after the merge
; presentation. update_chain_reaction_sidebar expires it from the normal input
; loop, so no gameplay or audio processing is delayed.
arm_chain_reaction_sidebar:
    lda #CHAIN_BANNER_FRAMES
    sta chain_banner_frames
    lda RTCLOK+2
    sta chain_banner_last
    rts

update_chain_reaction_sidebar:
    lda gameplay_input
    beq @done
    lda chain_banner_frames
    beq @done
    lda RTCLOK+2
    cmp chain_banner_last
    beq @done
    sta chain_banner_last
    dec chain_banner_frames
    bne @done
    jmp hide_chain_reaction_sidebar
@done:
    rts

; Format the multiplied 16-bit award as a right-aligned "+value" string.
; Inputs: score_delta_lo/hi. Output: merge_score_string. Clobbers A/X/Y,
; score_work_lo/hi, score_digit and text_index; leaves the award unchanged.
format_merge_score:
    lda score_delta_lo
    sta score_work_lo
    lda score_delta_hi
    sta score_work_hi
    ldx #0
@digit:
    stx text_index
    lda #0
    sta score_digit
@subtract:
    ldx text_index
    lda score_work_hi
    cmp score_div_hi,x
    bcc @store
    bne @can_subtract
    lda score_work_lo
    cmp score_div_lo,x
    bcc @store
@can_subtract:
    sec
    lda score_work_lo
    sbc score_div_lo,x
    sta score_work_lo
    lda score_work_hi
    sbc score_div_hi,x
    sta score_work_hi
    inc score_digit
    jmp @subtract
@store:
    lda score_digit
    clc
    adc #'0'
    ldx text_index
    sta score_string,x
    inx
    cpx #5
    bne @digit

    lda #' '
    ldx #5
@blank:
    sta merge_score_string,x
    dex
    bpl @blank
    lda #0
    sta merge_score_string+6
    ldy #0
@leading:
    lda score_string,y
    cmp #'0'
    bne @found
    cpy #4
    beq @found
    iny
    bne @leading
@found:
    sty text_index
    tya
    tax                         ; plus occupies the cell before the digits
    lda #'+'
    sta merge_score_string,x
    inx
@copy:
    lda score_string,y
    sta merge_score_string,x
    inx
    iny
    cpy #5
    bne @copy
    rts

; Display the current merge award in the left sidebar below the permanent
; score and above the mascot. The opaque 48x8 strip is restored by hide_callout.
show_merge_score:
    jsr format_merge_score
    lda #6
    sta blit_width
    lda #8
    sta blit_height
    lda #2                      ; center six bytes in the 10-byte sidebar
    sta blit_x
    lda #28                     ; between score digits and mascot
    sta blit_y
    jsr save_callout_underlay
    jsr clear_bitmap_rect
    lda #<merge_score_string
    sta zp_text
    lda #>merge_score_string
    sta zp_text+1
    lda blit_y
    ldx blit_x
    jmp draw_text

; Animate "2X", "3X", etc. diagonally away from the resolved die. The badge
; uses the bitmap font as a small sprite and restores every previous position
; before moving. Values above 9 display as 9X on the 5x5 board.
shoot_chain_multiplier:
    lda merge_depth
    cmp #10
    bcc :+
    lda #9
:
    clc
    adc #'0'
    sta chain_badge_string
    lda #'X'
    sta chain_badge_string+1
    lda #0
    sta chain_badge_string+2
    ldx active_index
    lda cell_x_bytes,x
    clc
    adc #1
    sta chain_badge_x
    cmp #23
    bcc @right
    lda #$FF
    bne @direction
@right:
    lda #1
@direction:
    sta chain_badge_dx
    lda cell_y_pixels,x
    clc
    adc #10
    sta chain_badge_y
    lda #0
    sta chain_badge_step
@step:
    lda chain_badge_x
    sta blit_x
    lda chain_badge_y
    sta blit_y
    lda #2
    sta blit_width
    lda #8
    sta blit_height
    jsr save_callout_underlay
    jsr clear_bitmap_rect
    lda #<chain_badge_string
    sta zp_text
    lda #>chain_badge_string
    sta zp_text+1
    lda blit_y
    ldx blit_x
    jsr draw_text
    lda #2
    jsr wait_frames
    jsr restore_callout_underlay
    lda chain_badge_x
    clc
    adc chain_badge_dx
    sta chain_badge_x
    dec chain_badge_y
    dec chain_badge_y
    inc chain_badge_step
    lda chain_badge_step
    cmp #5
    bne @step
    rts
