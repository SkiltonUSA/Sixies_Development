; ANTIC mode F (320x192, one bit per pixel) renderer.

FOOTER_LINE = 1
BOX_TOP_LEFT = 2
BOX_TOP = 3
BOX_TOP_RIGHT = 4
BOX_BOTTOM_LEFT = 5
BOX_BOTTOM = 6
BOX_BOTTOM_RIGHT = 7
CALLOUT_UNDERLAY = $9E60
HIRES_WHITE = $0E
GAME_GOLD_HUE = $10
GAME_CYAN_HUE = $A0
GAME_CYAN_BRIGHT = $AE

.segment "BSS"
text_column:        .res 1
text_row:           .res 1
text_index:         .res 1
glyph_row:          .res 1
blit_width:         .res 1
blit_height:        .res 1
blit_x:             .res 1
blit_y:             .res 1
blit_row:           .res 1
cell_index_temp:    .res 1
score_work_lo:      .res 1
score_work_hi:      .res 1
score_digit:        .res 1
score_string:       .res 6
preview_show_x:     .res 1
rle_count:          .res 1
rle_value:          .res 1
ripple_left:        .res 1
ripple_right:       .res 1
ripple_top:         .res 1
ripple_bottom:      .res 1
dli_middle_hue:     .res 1

.segment "DLIST"
; ANTIC wraps display-list DMA within a 1K block. Keep the complete 202-byte
; list in one block as code/assets grow ahead of RODATA.
display_list:
    .byte $70,$70,$70
    .byte $4F, <SCREEN, >SCREEN
    .repeat 23
        .byte $0F
    .endrepeat
    ; The gameplay logo occupies bitmap rows 1-24. Change from its gold hue
    ; to cyan after row 24; other pages leave DLI NMIs disabled.
    .byte $8F
    .repeat SCREEN_SPLIT-25
        .byte $0F
    .endrepeat
    ; ANTIC DMA cannot cross a 4K boundary. Restart at $9000 after 100
    ; 40-byte rows, leaving the final 96 bytes of the $8xxx page unused.
    .byte $4F, <SCREEN_SECOND, >SCREEN_SECOND
    .repeat 65
        .byte $0F
    .endrepeat
    ; Switch the horizontal rule and boxed controls back to gold at row 167.
    .byte $8F
    .repeat 25
        .byte $0F
    .endrepeat
    .byte $41, <display_list, >display_list

.segment "RODATA"
screen_row_lo:
    .repeat SCREEN_LINES, line
        .if line < SCREEN_SPLIT
            .byte <(SCREEN + line * SCREEN_BYTES)
        .else
            .byte <(SCREEN_SECOND + (line-SCREEN_SPLIT) * SCREEN_BYTES)
        .endif
    .endrepeat
screen_row_hi:
    .repeat SCREEN_LINES, line
        .if line < SCREEN_SPLIT
            .byte >(SCREEN + line * SCREEN_BYTES)
        .else
            .byte >(SCREEN_SECOND + (line-SCREEN_SPLIT) * SCREEN_BYTES)
        .endif
    .endrepeat

cell_x_bytes:       .byte 10,14,18,22,26, 10,14,18,22,26, 10,14,18,22,26, 10,14,18,22,26, 10,14,18,22,26
cell_y_pixels:      .byte 26,26,26,26,26, 54,54,54,54,54, 82,82,82,82,82, 110,110,110,110,110, 138,138,138,138,138

dice_lo:            .byte <(dice_asset + 0*96), <(dice_asset + 1*96), <(dice_asset + 2*96)
                    .byte <(dice_asset + 3*96), <(dice_asset + 4*96), <(dice_asset + 5*96)
dice_hi:            .byte >(dice_asset + 0*96), >(dice_asset + 1*96), >(dice_asset + 2*96)
                    .byte >(dice_asset + 3*96), >(dice_asset + 4*96), >(dice_asset + 5*96)
callout_lo:         .repeat 10, index
                        .byte <(callout_asset + index*240)
                    .endrepeat
callout_hi:         .repeat 10, index
                        .byte >(callout_asset + index*240)
                    .endrepeat

score_div_lo:       .byte <10000,<1000,<100,<10,<1
score_div_hi:       .byte >10000,>1000,>100,>10,>1

text_score:         .asciiz "SCORE"
text_new_game:      .asciiz "[N]EW GAME"
text_instructions:  .asciiz "[I]NSTRUCTIONS"
text_title_prompt:  .asciiz "FIRE SPACE START   C CREDITS"
text_64k:           .asciiz "ATARI 800XL 64K"
text_128k:          .asciiz "ATARI 130XE 128K ENHANCED"
text_restart:       .asciiz "PRESS TO VIEW HIGH SCORES"
text_new_confirm:   .asciiz "NEW GAME  Y YES  N NO"

title_logo_asset:   .incbin "build/assets/title_logo.rle"
presents_asset:     .incbin "build/assets/presents.rle"
instructions_asset: .incbin "build/assets/instructions.rle"
game_over_asset:    .incbin "build/assets/game_over.rle"
game_grid_asset:    .incbin "build/assets/game_grid.rle"
mascot_asset:       .incbin "build/assets/mascot.bin"
dice_asset:         .incbin "build/assets/dice.bin"
invalid_asset:      .incbin "build/assets/invalid.bin"
occupied_asset:     .incbin "build/assets/occupied.bin"
merge_star_asset:   .incbin "build/assets/merge_star.bin"
callout_asset:      .incbin "build/assets/callouts.bin"
font_asset:         .incbin "build/assets/font.bin"

.segment "AUXCODE"

video_init:
    lda #0
    sta SDMCTL
    sta DMACTL
    sta COLOR0
    sta COLOR2
    sta COLOR3
    sta COLOR4
    sta COLPF0
    sta COLPF2
    sta COLPF3
    sta COLBK
    lda #HIRES_WHITE
    sta COLOR1
    sta COLPF1
    lda #<display_list
    sta SDLSTL
    sta DLISTL
    lda #>display_list
    sta SDLSTL+1
    sta DLISTH
    lda #0
    sta GPRIOR
    sta PRIOR
    lda #$22
    sta SDMCTL
    sta DMACTL
    rts

; Both marked rows call one scanline-aware handler. This avoids phase errors
; when a page finishes drawing after the first DLI position in the frame.
color_band_dli:
    pha
    lda VCOUNT
    cmp #60
    bcs @footer
    lda dli_middle_hue
    jmp @set
@footer:
    lda #GAME_GOLD_HUE
@set:
    sta WSYNC
    sta COLPF2
    pla
    rti

arm_gameplay_dli:
    lda #GAME_CYAN_HUE
    bne arm_color_band_dli

; The instruction page uses the same display-list split rows with a different
; middle color: gold header, white body, then gold continuation box.
arm_instructions_dli:
    lda #0
arm_color_band_dli:
    sta dli_middle_hue
    lda #<color_band_dli
    sta VDSLST
    lda #>color_band_dli
    sta VDSLST+1
    lda #$C0
    sta NMIEN
    rts

.segment "CODE"

; Expand a complete 7936-byte physical ANTIC screen from zp_asset to $8000.
; Packet bit 7 selects repeat/literal; low 7 bits store count minus one.
unpack_screen_rle:
    lda #<SCREEN
    sta zp_screen
    lda #>SCREEN
    sta zp_screen+1
@packet:
    jsr rle_read_byte
    cmp #$80
    bcs @repeat
    clc
    adc #1
    sta rle_count
@literal_loop:
    jsr rle_read_byte
    jsr rle_write_byte
    dec rle_count
    bne @literal_loop
    beq @check_done
@repeat:
    and #$7F
    clc
    adc #1
    sta rle_count
    jsr rle_read_byte
    sta rle_value
@repeat_loop:
    lda rle_value
    jsr rle_write_byte
    dec rle_count
    bne @repeat_loop
@check_done:
    lda zp_screen+1
    cmp #>SCREEN_PHYSICAL_END
    bne @packet
    lda zp_screen
    cmp #<SCREEN_PHYSICAL_END
    bne @packet
    rts

rle_read_byte:
    ldy #0
    lda (zp_asset),y
    inc zp_asset
    bne :+
    inc zp_asset+1
:
    rts

rle_write_byte:
    ldy #0
    sta (zp_screen),y
    inc zp_screen
    bne :+
    inc zp_screen+1
:
    rts

set_screen_row:
    stx zp_temp
    tax
    lda screen_row_lo,x
    sta zp_screen
    lda screen_row_hi,x
    sta zp_screen+1
    ldx zp_temp
    rts

; zp_text points to a zero-terminated string; A=row, X=byte column.
draw_text:
    sta text_row
    stx text_column
    lda #0
    sta text_index
@next:
    ldy text_index
    lda (zp_text),y
    beq @done
    jsr draw_character
    inc text_column
    inc text_index
    bne @next
@done:
    rts

; A = ASCII character.
draw_character:
    sta zp_target
    lda #0
    sta zp_asset+1
    lda zp_target
    asl
    rol zp_asset+1
    asl
    rol zp_asset+1
    asl
    rol zp_asset+1
    sta zp_asset
    clc
    lda zp_asset
    adc #<font_asset
    sta zp_asset
    lda zp_asset+1
    adc #>font_asset
    sta zp_asset+1
    lda #0
    sta glyph_row
@row:
    lda text_row
    clc
    adc glyph_row
    jsr set_screen_row
    ldy glyph_row
    lda (zp_asset),y
    ldy text_column
    sta (zp_screen),y
    inc glyph_row
    lda glyph_row
    cmp #8
    bne @row
    rts

; Generic byte-aligned OR blitter. zp_asset, blit_width/height/x/y are inputs.
blit_or:
    lda #0
    sta blit_row
@row:
    lda blit_y
    clc
    adc blit_row
    jsr set_screen_row
    ldy #0
@byte:
    lda (zp_asset),y
    sty zp_temp
    ldy blit_x
    ora (zp_screen),y
    sta (zp_screen),y
    ldy zp_temp
    inc blit_x
    iny
    cpy blit_width
    bne @byte
    tya
    clc
    adc zp_asset
    sta zp_asset
    bcc :+
    inc zp_asset+1
:
    tya
    sec
    sbc blit_width
    ; Restore x by subtracting the width advanced by the inner loop.
    lda blit_x
    sec
    sbc blit_width
    sta blit_x
    inc blit_row
    lda blit_row
    cmp blit_height
    bne @row
    rts

; Generic byte-aligned subtractive blitter. Every set asset pixel clears its
; destination pixel, allowing a black marker to cut through a white die.
blit_clear:
    lda #0
    sta blit_row
@row:
    lda blit_y
    clc
    adc blit_row
    jsr set_screen_row
    ldy #0
@byte:
    lda (zp_asset),y
    eor #$FF
    sty zp_temp
    ldy blit_x
    and (zp_screen),y
    sta (zp_screen),y
    ldy zp_temp
    inc blit_x
    iny
    cpy blit_width
    bne @byte
    tya
    clc
    adc zp_asset
    sta zp_asset
    bcc :+
    inc zp_asset+1
:
    lda blit_x
    sec
    sbc blit_width
    sta blit_x
    inc blit_row
    lda blit_row
    cmp blit_height
    bne @row
    rts

; Generic byte-aligned XOR blitter. Used by the merge star so it remains
; visible over both an upgraded die and the empty cell left by cleared sixes.
blit_xor:
    lda #0
    sta blit_row
@row:
    lda blit_y
    clc
    adc blit_row
    jsr set_screen_row
    ldy #0
@byte:
    lda (zp_asset),y
    sty zp_temp
    ldy blit_x
    eor (zp_screen),y
    sta (zp_screen),y
    ldy zp_temp
    inc blit_x
    iny
    cpy blit_width
    bne @byte
    tya
    clc
    adc zp_asset
    sta zp_asset
    bcc :+
    inc zp_asset+1
:
    lda blit_x
    sec
    sbc blit_width
    sta blit_x
    inc blit_row
    lda blit_row
    cmp blit_height
    bne @row
    rts

; Clear a byte-aligned rectangle. Inputs are blit_x/y/width/height.
clear_bitmap_rect:
    lda #0
    sta blit_row
@row:
    lda blit_y
    clc
    adc blit_row
    jsr set_screen_row
    ldy blit_x
    ldx blit_width
    lda #0
@byte:
    sta (zp_screen),y
    iny
    dex
    bne @byte
    inc blit_row
    lda blit_row
    cmp blit_height
    bne @row
    rts

; A = value 1..6, X = board cell index.
draw_die_at_cell:
    pha
    lda cell_x_bytes,x
    sta blit_x
    lda cell_y_pixels,x
    clc
    adc #2
    sta blit_y
    pla
    sec
    sbc #1
    tax
    lda dice_lo,x
    sta zp_asset
    lda dice_hi,x
    sta zp_asset+1
    lda #4
    sta blit_width
    lda #24
    sta blit_height
    jsr blit_or
    rts

draw_invalid_at_cell:
    tax
    lda cell_x_bytes,x
    sta blit_x
    lda cell_y_pixels,x
    clc
    adc #2
    sta blit_y
    lda #<invalid_asset
    sta zp_asset
    lda #>invalid_asset
    sta zp_asset+1
    lda #4
    sta blit_width
    lda #24
    sta blit_height
    jmp blit_clear

; A = board-cell index. Clear its 24-line interior while preserving the
; four-pixel vertical grid borders held in the outer two bytes.
clear_cell_interior:
    tax
    stx cell_index_temp
    lda cell_x_bytes,x
    sta blit_x
    lda cell_y_pixels,x
    clc
    adc #2
    sta blit_y
    lda #0
    sta blit_row
@row:
    lda blit_y
    clc
    adc blit_row
    jsr set_screen_row
    ldy blit_x
    lda (zp_screen),y
    and #$F0
    sta (zp_screen),y
    iny
    lda #0
    sta (zp_screen),y
    iny
    sta (zp_screen),y
    iny
    lda (zp_screen),y
    and #$0F
    sta (zp_screen),y
    inc blit_row
    lda blit_row
    cmp #24
    bne @row
    rts

draw_occupied_at_cell:
    jsr clear_cell_interior
    ldx cell_index_temp
    lda cell_x_bytes,x
    sta blit_x
    lda cell_y_pixels,x
    clc
    adc #2
    sta blit_y
    lda #<occupied_asset
    sta zp_asset
    lda #>occupied_asset
    sta zp_asset+1
    lda #4
    sta blit_width
    lda #24
    sta blit_height
    jmp blit_or

draw_board_dice:
    ldx #0
@loop:
    stx cell_index_temp
    lda board,x
    beq @next
    ldx cell_index_temp
    jsr draw_die_at_cell
@next:
    ldx cell_index_temp
    inx
    cpx #25
    bne @loop
    rts

; A = board-cell index. Remove only the preview/invalid-marker pixels from the
; 24-line die interior, preserving the four-pixel grid border at either side.
; If the cursor was over an occupied cell, restore that permanent board die.
restore_cell_under_preview:
    jsr clear_cell_interior
    ldx cell_index_temp
    lda board,x
    beq @done
    jsr draw_die_at_cell
@done:
    rts

; Remove the preview at its current cursor/orientation. This is the first half
; of a dirty-cell update; draw_piece_preview renders the new state afterward.
erase_piece_preview:
    lda piece_visible
    beq @done
    jsr placement_valid
    lda active_index
    jsr restore_cell_under_preview
    lda piece_count
    cmp #2
    bne @done
    jsr compute_second_index
    bcc @done
    jsr restore_cell_under_preview
@done:
    rts

; Refresh only the cells modified by the current merge group.
redraw_group_cells:
    ldy #0
@cell:
    sty text_index
    lda group_queue,y
    jsr restore_cell_under_preview
    ldy text_index
    iny
    cpy group_count
    bne @cell
    rts

; A = hovering die value, X = target cell. An occupied cell temporarily shows
; the diagonal hatch. Empty targets receive an X only for a boundary error;
; the hatch alone explains a placement blocked by an occupied partner cell.
draw_preview_at_cell:
    stx cell_index_temp
    pha
    lda board,x
    beq @empty
    pla
    txa
    jmp draw_occupied_at_cell
@empty:
    pla
    ldx cell_index_temp
    jsr draw_die_at_cell
    lda preview_show_x
    beq @done
    lda cell_index_temp
    jmp draw_invalid_at_cell
@done:
    rts

draw_piece_preview:
    lda piece_visible
    beq @done
    jsr placement_valid
    lda #0
    rol
    eor #1
    sta preview_show_x
    beq @render
    ; A geometrically valid occupied target supplies the complete warning, so
    ; suppress the X on its empty partner. Preserve the X for off-grid pieces.
    ldx active_index
    lda board,x
    bne @hide_x
    lda piece_count
    cmp #2
    bne @render
    jsr compute_second_index
    bcc @render
    tax
    lda board,x
    beq @render
@hide_x:
    lda #0
    sta preview_show_x
@render:
    ldx active_index
    lda piece_a
    jsr draw_preview_at_cell
    lda piece_count
    cmp #2
    bne @done
    jsr compute_second_index
    bcc @done
    sta placed_second
    tax
    lda piece_b
    jsr draw_preview_at_cell
@done:
    rts

draw_mascot:
    lda #<mascot_asset
    sta zp_asset
    lda #>mascot_asset
    sta zp_asset+1
    lda #10
    sta blit_width
    lda #100
    sta blit_height
    lda #0
    sta blit_x
    lda #52
    sta blit_y
    jmp blit_or

draw_piece_sidebar:
    lda piece_a
    ldx #31
    jsr draw_sidebar_die
    lda piece_count
    cmp #2
    bne @done
    lda piece_b
    ldx #35
    jsr draw_sidebar_die
@done:
    rts

; A=value, X=x byte; fixed y=64.
draw_sidebar_die:
    stx blit_x
    sec
    sbc #1
    tax
    lda dice_lo,x
    sta zp_asset
    lda dice_hi,x
    sta zp_asset+1
    lda #4
    sta blit_width
    lda #24
    sta blit_height
    lda #64
    sta blit_y
    jmp blit_or

draw_score:
    lda #<text_score
    sta zp_text
    lda #>text_score
    sta zp_text+1
    lda #4
    ldx #1
    jsr draw_text
    lda score_lo
    sta score_work_lo
    lda score_hi
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
    lda #0
    sta score_string+5
    lda #<score_string
    sta zp_text
    lda #>score_string
    sta zp_text+1
    lda #13
    ldx #1
    jmp draw_text

redraw_score_digits:
    lda #1
    sta blit_x
    lda #13
    sta blit_y
    lda #5
    sta blit_width
    lda #8
    sta blit_height
    jsr clear_bitmap_rect
    jmp draw_score

redraw_piece_sidebar:
    lda #31
    sta blit_x
    lda #64
    sta blit_y
    lda #8
    sta blit_width
    lda #24
    sta blit_height
    jsr clear_bitmap_rect
    jmp draw_piece_sidebar

refresh_turn_display:
    jsr redraw_score_digits
    jsr redraw_piece_sidebar
    jmp draw_piece_preview

; X = starting byte column, Y = width in 8-pixel glyphs. Draw a fixed-height
; clipped-corner box using custom glyphs in the existing 2K font allocation.
draw_footer_box:
    stx blit_x
    sty blit_width
    stx text_column
    lda #174
    sta text_row
    lda #BOX_TOP_LEFT
    jsr draw_character
    inc text_column
    lda blit_width
    sec
    sbc #2
    tax
@top:
    lda #BOX_TOP
    jsr draw_character
    inc text_column
    dex
    bne @top
    lda #BOX_TOP_RIGHT
    jsr draw_character

    lda blit_x
    sta text_column
    lda #182
    sta text_row
    lda #BOX_BOTTOM_LEFT
    jsr draw_character
    inc text_column
    lda blit_width
    sec
    sbc #2
    tax
@bottom:
    lda #BOX_BOTTOM
    jsr draw_character
    inc text_column
    dex
    bne @bottom
    lda #BOX_BOTTOM_RIGHT
    jmp draw_character

draw_game_footer:
    lda #167
    sta text_row
    lda #0
    sta text_column
    ldx #40
@line:
    lda #FOOTER_LINE
    jsr draw_character
    inc text_column
    dex
    bne @line
    ldx #1
    ldy #14
    jsr draw_footer_box
    ldx #23
    ldy #16
    jsr draw_footer_box
    lda #<text_new_game
    sta zp_text
    lda #>text_new_game
    sta zp_text+1
    lda #178
    ldx #3
    jsr draw_text
    lda #<text_instructions
    sta zp_text
    lda #>text_instructions
    sta zp_text+1
    lda #178
    ldx #24
    jmp draw_text

render_game:
    jsr video_update_begin
    lda #<game_grid_asset
    sta zp_asset
    lda #>game_grid_asset
    sta zp_asset+1
    jsr unpack_screen_rle
    jsr draw_score
    jsr draw_board_dice
    jsr draw_piece_preview
    jsr draw_mascot
    jsr draw_piece_sidebar
    jsr draw_game_footer
    ; Mode F takes foreground luminance from PF1 and hue from PF2. Start each
    ; frame gold for the isolated logo; the display-list interrupt changes
    ; subsequent rows to cyan while both backgrounds retain zero luminance.
    lda #GAME_GOLD_HUE
    sta COLOR2
    sta COLPF2
    jsr video_update_end
    jmp arm_gameplay_dli

show_title:
    jsr video_update_begin
    lda #<title_logo_asset
    sta zp_asset
    lda #>title_logo_asset
    sta zp_asset+1
    jsr unpack_screen_rle
    lda #<text_title_prompt
    sta zp_text
    lda #>text_title_prompt
    sta zp_text+1
    lda #154
    ldx #8
    jsr draw_text
    lda ram_kb
    cmp #128
    bne @64
    lda #<text_128k
    sta zp_text
    lda #>text_128k
    sta zp_text+1
    bne @machine
@64:
    lda #<text_64k
    sta zp_text
    lda #>text_64k
    sta zp_text+1
@machine:
    lda #176
    ldx #8
    jsr draw_text
    jmp video_update_end

show_presents:
    jsr video_update_begin
    lda #<presents_asset
    sta zp_asset
    lda #>presents_asset
    sta zp_asset+1
    jsr unpack_screen_rle
    jmp video_update_end

show_instructions:
    jsr video_update_begin
    lda #<instructions_asset
    sta zp_asset
    lda #>instructions_asset
    sta zp_asset+1
    jsr unpack_screen_rle
    lda #GAME_GOLD_HUE
    sta COLOR2
    sta COLPF2
    jsr video_update_end
    jmp arm_instructions_dli

show_new_game_confirm:
    lda #<text_new_confirm
    sta zp_text
    lda #>text_new_confirm
    sta zp_text+1
    lda #16
    ldx #10
    jsr draw_text
    rts

show_game_over:
    jsr video_update_begin
    lda #<game_over_asset
    sta zp_asset
    lda #>game_over_asset
    sta zp_asset+1
    jsr unpack_screen_rle
    jsr draw_score
    lda #<text_restart
    sta zp_text
    lda #>text_restart
    sta zp_text+1
    lda #150
    ldx #8
    jsr draw_text
    jmp video_update_end

; A = callout index 0..9. Center it on the resolved merge cell, clamping the
; 80-pixel banner inside the 160-pixel board. Save and black out the covered
; pixels first so the bright artwork remains readable over dice and grid lines.
show_callout:
    tax
    lda callout_lo,x
    sta zp_asset
    lda callout_hi,x
    sta zp_asset+1
    lda #10
    sta blit_width
    lda #24
    sta blit_height
    ldx active_index
    lda cell_x_bytes,x
    sec
    sbc #3
    cmp #10
    bcs @left_ok
    lda #10
@left_ok:
    cmp #21
    bcc @right_ok
    lda #20
@right_ok:
    sta blit_x
    lda cell_y_pixels,x
    clc
    adc #2
    sta blit_y
    jsr save_callout_underlay
    jsr clear_bitmap_rect
    jmp blit_or

hide_callout:
    jmp restore_callout_underlay

; A = resolved board-cell index. XOR the supplied four-point star over it.
show_merge_star:
    tax
    lda cell_x_bytes,x
    sta blit_x
    lda cell_y_pixels,x
    clc
    adc #2
    sta blit_y
    lda #<merge_star_asset
    sta zp_asset
    lda #>merge_star_asset
    sta zp_asset+1
    lda #4
    sta blit_width
    lda #24
    sta blit_height
    jmp blit_xor

.segment "AUXCODE"

; Wait A display frames and service POKEY each frame.
wait_frames:
    sta zp_frames
@frame:
    lda RTCLOK+2
    sta zp_old_frame
@wait:
    lda RTCLOK+2
    cmp zp_old_frame
    beq @wait
    lda #0
    sta ATRACT
    jsr sound_update
    dec zp_frames
    bne @frame
    rts

.segment "CODE"

video_update_begin:
    lda #0
    sta NMIEN
    sta SDMCTL
    sta DMACTL
    lda #HIRES_WHITE
    sta COLOR1
    sta COLPF1
    lda #0
    sta COLOR2
    sta COLPF2
    rts

video_update_end:
    lda #$22
    sta SDMCTL
    sta DMACTL
    lda #$40
    sta NMIEN
    rts

.segment "AUXCODE"

; Flash the complete display when a group of sixes disappears. Swapping the
; mode-F foreground and background colors is instantaneous and leaves every
; screen byte untouched, avoiding a full-frame redraw or tear.
flash_six_clear:
    lda #$40
    sta NMIEN
    lda #GAME_CYAN_BRIGHT
    sta COLOR4
    sta COLBK
    sta COLOR2
    sta COLPF2
    lda #0
    sta COLOR1
    sta COLPF1
    lda #5
    jsr wait_frames
    lda #0
    sta COLOR4
    sta COLBK
    lda #GAME_GOLD_HUE
    sta COLOR2
    sta COLPF2
    lda #HIRES_WHITE
    sta COLOR1
    sta COLPF1
    jmp arm_gameplay_dli

; Preserve the exact 80x24 bitmap below a callout. X is a linear 0..239
; buffer index; blit_row selects the physical ANTIC row.
save_callout_underlay:
    ldx #0
    lda #0
    sta blit_row
@row:
    lda blit_y
    clc
    adc blit_row
    jsr set_screen_row
    ldy blit_x
    lda #10
    sta zp_temp
@byte:
    lda (zp_screen),y
    sta CALLOUT_UNDERLAY,x
    inx
    iny
    dec zp_temp
    bne @byte
    inc blit_row
    lda blit_row
    cmp #24
    bne @row
    rts

; Restore the saved bitmap after the half-second callout hold.
restore_callout_underlay:
    ldx #0
    lda #0
    sta blit_row
@row:
    lda blit_y
    clc
    adc blit_row
    jsr set_screen_row
    ldy blit_x
    lda #10
    sta zp_temp
@byte:
    lda CALLOUT_UNDERLAY,x
    sta (zp_screen),y
    inx
    iny
    dec zp_temp
    bne @byte
    inc blit_row
    lda blit_row
    cmp #24
    bne @row
    rts

; Pulse the resolved row and column inward from all four grid edges. A face-4
; merge also brings four diagonal arms inward from the corners. Each step is
; inverted for two frames and then restored before advancing.
run_merge_grid_ripple:
    lda active_index
    ldx #0
@find_row:
    cmp #5
    bcc @position_ready
    sec
    sbc #5
    inx
    bne @find_row
@position_ready:
    sta scan_index
    stx weight_index
    lda #0
    sta queue_head
@step:
    jsr toggle_merge_ripple_step
    lda #2
    jsr wait_frames
    jsr toggle_merge_ripple_step
    inc queue_head
    lda queue_head
    cmp #5
    bne @step
    rts

; Build the current edge positions. queue_ripple_xy removes duplicate cells
; when orthogonal or diagonal arms converge at the resolved die.
toggle_merge_ripple_step:
    lda #0
    sta group_count

    lda queue_head
    cmp scan_index
    bcc @left_ready
    lda scan_index
@left_ready:
    sta ripple_left

    lda #4
    sec
    sbc queue_head
    cmp scan_index
    bcs @right_ready
    lda scan_index
@right_ready:
    sta ripple_right

    ldx queue_head
    cpx weight_index
    bcc @top_ready
    ldx weight_index
@top_ready:
    stx ripple_top

    lda #4
    sec
    sbc queue_head
    tax
    cpx weight_index
    bcs @bottom_ready
    ldx weight_index
@bottom_ready:
    stx ripple_bottom

    lda ripple_left
    ldx weight_index
    jsr queue_ripple_xy
    lda ripple_right
    ldx weight_index
    jsr queue_ripple_xy
    lda scan_index
    ldx ripple_top
    jsr queue_ripple_xy
    lda scan_index
    ldx ripple_bottom
    jsr queue_ripple_xy

    lda group_value
    cmp #4
    bne @done
    lda ripple_left
    ldx ripple_top
    jsr queue_ripple_xy
    lda ripple_right
    ldx ripple_top
    jsr queue_ripple_xy
    lda ripple_left
    ldx ripple_bottom
    jsr queue_ripple_xy
    lda ripple_right
    ldx ripple_bottom
    jsr queue_ripple_xy
@done:
    rts

; A = column, X = row. Toggle each candidate no more than once per step.
queue_ripple_xy:
    sta zp_temp
    lda row_offsets,x
    clc
    adc zp_temp
    ldx #0
@check:
    cpx group_count
    beq @add
    cmp group_queue,x
    beq @done
    inx
    bne @check
@add:
    ldx group_count
    sta group_queue,x
    inc group_count
    jmp invert_ripple_cell
@done:
    rts

; A = board-cell index. Invert only the 24-line interior, retaining the four
; vertical grid-border pixels at each side of the 32-pixel cell.
invert_ripple_cell:
    tax
    lda cell_x_bytes,x
    sta blit_x
    lda cell_y_pixels,x
    clc
    adc #2
    sta blit_y
    lda #0
    sta blit_row
@row:
    lda blit_y
    clc
    adc blit_row
    jsr set_screen_row
    ldy blit_x
    lda (zp_screen),y
    eor #$0F
    sta (zp_screen),y
    iny
    lda (zp_screen),y
    eor #$FF
    sta (zp_screen),y
    iny
    lda (zp_screen),y
    eor #$FF
    sta (zp_screen),y
    iny
    lda (zp_screen),y
    eor #$F0
    sta (zp_screen),y
    inc blit_row
    lda blit_row
    cmp #24
    bne @row
    rts
