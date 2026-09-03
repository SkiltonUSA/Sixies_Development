; Platform-independent Sixies rules, implemented in 6502 assembly.
; This follows apple2/RULES_README.md: 2/3 paired pieces, unlockable 4/5
; singles, weighted forced singles, complete orthogonal groups, origin-first
; double resolution, and the 50-point value-6 removal bonus.

.segment "BSS"
board:              .res 25
visited:            .res 25
group_queue:        .res 25
face_weights:       .res 5
piece_count:        .res 1
piece_a:            .res 1
piece_b:            .res 1
cursor_x:           .res 1
cursor_y:           .res 1
orientation:        .res 1
score_lo:           .res 1
score_hi:           .res 1
rng_state:          .res 1
single_mode:        .res 1
game_over:          .res 1
piece_visible:      .res 1
four_unlocked:      .res 1
five_unlocked:      .res 1
eligible_count:     .res 1
active_index:       .res 1
placed_second:      .res 1
group_value:        .res 1
group_count:        .res 1
queue_head:         .res 1
queue_tail:         .res 1
scan_index:         .res 1
weight_index:       .res 1
weight_total:       .res 1
merge_depth:        .res 1
score_delta_lo:     .res 1
score_delta_hi:     .res 1

.segment "RODATA"
row_offsets:        .byte 0, 5, 10, 15, 20
cell_columns:       .byte 0,1,2,3,4, 0,1,2,3,4, 0,1,2,3,4, 0,1,2,3,4, 0,1,2,3,4
cell_rows:          .byte 0,0,0,0,0, 1,1,1,1,1, 2,2,2,2,2, 3,3,3,3,3, 4,4,4,4,4
pair_first:         .byte 1,1,2,2,3,3
pair_second:        .byte 2,3,3,4,3,4

.segment "CODE"

new_game:
    lda #0
    ldx #24
@clear:
    sta board,x
    dex
    bpl @clear
    sta score_lo
    sta score_hi
    sta game_over
    sta single_mode
    lda RTCLOK+2
    eor RANDOM
    ora #1
    sta rng_state
    jsr spawn_piece
    rts

random8:
    lda rng_state
    asl
    bcc :+
    eor #$1D
:
    bne :+
    lda #$A5
:
    sta rng_state
    rts

; X = modulus (1..255), returns A in 0..X-1.
random_mod_x:
    stx zp_modulus
    jsr random8
@reduce:
    cmp zp_modulus
    bcc @done
    sec
    sbc zp_modulus
    bcs @reduce
@done:
    rts

; A = board value, returns X = count.
count_board_value:
    sta zp_target
    ldx #0
    ldy #0
@loop:
    lda board,y
    cmp zp_target
    bne :+
    inx
:
    iny
    cpy #25
    bne @loop
    rts

has_empty_cell:
    ldx #0
@loop:
    lda board,x
    beq @yes
    inx
    cpx #25
    bne @loop
    lda #0
    rts
@yes:
    lda #1
    rts

has_adjacent_empty_pair:
    ldx #0
@loop:
    lda board,x
    bne @next
    lda cell_columns,x
    cmp #4
    beq @down
    lda board+1,x
    beq @yes
@down:
    lda cell_rows,x
    cmp #4
    beq @next
    lda board+5,x
    beq @yes
@next:
    inx
    cpx #25
    bne @loop
    lda #0
    rts
@yes:
    lda #1
    rts

spawn_piece:
    lda #0
    sta piece_visible
    lda #4
    jsr count_board_value
    cpx #3
    lda #0
    rol
    sta four_unlocked
    lda #5
    jsr count_board_value
    cpx #4
    lda #0
    rol
    sta five_unlocked

    lda #3
    clc
    adc four_unlocked
    adc five_unlocked
    sta eligible_count

    jsr has_adjacent_empty_pair
    sta zp_adjacent
    eor #1
    sta single_mode
    lda zp_adjacent
    beq @single
    ldx #3
    jsr random_mod_x
    beq @single

@pair:
    ldx #6
    jsr random_mod_x
    tax
    lda #2
    sta piece_count
    lda pair_first,x
    sta piece_a
    lda pair_second,x
    sta piece_b
    jmp @position

@single:
    lda #1
    sta piece_count
    lda #0
    sta piece_b
    lda single_mode
    beq @normal_single
    ldx #3
    jsr random_mod_x
    beq @normal_single
    jsr weighted_surrounding_face
    bne @store_single
@normal_single:
    ldx eligible_count
    jsr random_mod_x
    clc
    adc #1
@store_single:
    sta piece_a

@position:
    lda #2
    sta cursor_x
    sta cursor_y
    lda #0
    sta orientation
    lda #1
    sta piece_visible
    lda piece_count
    cmp #2
    bne @check_single
    lda zp_adjacent
    bne @playable
@check_single:
    jsr has_empty_cell
    bne @playable
    lda #1
    sta game_over
@playable:
    rts

; Returns a weighted eligible face in A, or zero when no eligible neighbor
; faces surround an empty cell.
weighted_surrounding_face:
    lda #0
    ldx #4
@clear_weights:
    sta face_weights,x
    dex
    bpl @clear_weights
    sta weight_total
    sta scan_index
@scan:
    ldx scan_index
    lda board,x
    beq @next
    cmp #6
    bcs @next
    cmp #4
    bne :+
    lda four_unlocked
    beq @next
    lda #4
:
    cmp #5
    bne :+
    lda five_unlocked
    beq @next
    lda #5
:
    sec
    sbc #1
    sta weight_index

    ldx scan_index
    lda cell_columns,x
    beq @right
    txa
    sec
    sbc #1
    jsr add_empty_neighbor_weight
@right:
    ldx scan_index
    lda cell_columns,x
    cmp #4
    beq @up
    txa
    clc
    adc #1
    jsr add_empty_neighbor_weight
@up:
    ldx scan_index
    lda cell_rows,x
    beq @down
    txa
    sec
    sbc #5
    jsr add_empty_neighbor_weight
@down:
    ldx scan_index
    lda cell_rows,x
    cmp #4
    beq @next
    txa
    clc
    adc #5
    jsr add_empty_neighbor_weight
@next:
    inc scan_index
    lda scan_index
    cmp #25
    bne @scan

    lda weight_total
    beq @none
    tax
    jsr random_mod_x
    sta zp_choice
    ldx #0
@choose:
    lda zp_choice
    cmp face_weights,x
    bcc @chosen
    sec
    sbc face_weights,x
    sta zp_choice
    inx
    cpx #5
    bne @choose
@none:
    lda #0
    rts
@chosen:
    txa
    clc
    adc #1
    rts

add_empty_neighbor_weight:
    tay
    lda board,y
    bne @done
    ldx weight_index
    inc face_weights,x
    inc weight_total
@done:
    rts

; Converts cursor_x/cursor_y to origin index and computes the second cell.
; Carry set on geometrically valid placement, clear otherwise.
placement_valid:
    ldy cursor_y
    lda row_offsets,y
    clc
    adc cursor_x
    sta active_index
    tax
    lda board,x
    bne @invalid
    lda piece_count
    cmp #2
    bne @valid_single
    jsr compute_second_index
    bcc @invalid
    sta placed_second
    tax
    lda board,x
    bne @invalid
    sec
    rts
@valid_single:
    lda #$FF
    sta placed_second
    sec
    rts
@invalid:
    clc
    rts

compute_second_index:
    lda orientation
    beq @right
    cmp #1
    beq @down
    cmp #2
    beq @left
@up:
    lda cursor_y
    beq @bad
    lda active_index
    sec
    sbc #5
    sec
    rts
@right:
    lda cursor_x
    cmp #4
    beq @bad
    lda active_index
    clc
    adc #1
    sec
    rts
@down:
    lda cursor_y
    cmp #4
    beq @bad
    lda active_index
    clc
    adc #5
    sec
    rts
@left:
    lda cursor_x
    beq @bad
    lda active_index
    sec
    sbc #1
    sec
    rts
@bad:
    clc
    rts

place_current_piece:
    jsr placement_valid
    bcc @invalid
    lda #0
    sta piece_visible
    sta merge_depth
    ldx active_index
    lda piece_a
    sta board,x
    lda piece_count
    cmp #2
    bne @resolve_origin
    ldx placed_second
    lda piece_b
    sta board,x
@resolve_origin:
    lda active_index
    jsr resolve_at
    lda piece_count
    cmp #2
    bne @spawn
    ldx placed_second
    lda board,x
    beq @spawn
    txa
    jsr resolve_at
@spawn:
    jsr spawn_piece
    sec
    rts
@invalid:
    jsr play_invalid_sound
    clc
    rts

; A = active board index. Repeats at the same location for chain merges.
resolve_at:
    sta active_index
@again:
    jsr find_group
    lda group_count
    cmp #3
    bcs :+
    jmp @done
:
    inc merge_depth
    jsr score_group
    ldy #0
@clear_group:
    ldx group_queue,y
    lda #0
    sta board,x
    iny
    cpy group_count
    bne @clear_group
    lda group_value
    cmp #6
    beq @animate
    clc
    adc #1
    ldx active_index
    sta board,x
@animate:
    jsr redraw_group_cells
    jsr redraw_score_digits
    lda group_value
    jsr play_merge_sound
    ; Flash the supplied four-point star at the resolved die before the word
    ; callout. XOR keeps it visible over upgraded dice and cleared six cells.
    lda active_index
    jsr show_merge_star
    lda #3
    jsr wait_frames
    lda active_index
    jsr show_merge_star
    lda #2
    jsr wait_frames
    lda active_index
    jsr show_merge_star
    lda #3
    jsr wait_frames
    lda active_index
    jsr show_merge_star
    lda group_value
    cmp #4
    beq @fives
    cmp #5
    beq @sixies
    lda merge_depth
    cmp #2
    bcs @awesome
    jsr random8
    and #7
    cmp #7
    bne @show
    lda #9
    bne @show
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
    lda #8
    jsr wait_frames
    lda text_index
    jsr show_callout
    ldx active_index
    lda board,x
    beq @done
    jmp @again
@done:
    rts

find_group:
    ldx active_index
    lda board,x
    sta group_value
    lda #0
    ldx #24
@clear_seen:
    sta visited,x
    dex
    bpl @clear_seen
    sta queue_head
    lda #1
    sta queue_tail
    ldx active_index
    sta visited,x
    txa
    sta group_queue
@loop:
    lda queue_head
    cmp queue_tail
    beq @finished
    tax
    lda group_queue,x
    sta scan_index
    inc queue_head
    tax
    lda cell_columns,x
    beq @right
    txa
    sec
    sbc #1
    jsr try_group_neighbor
@right:
    ldx scan_index
    lda cell_columns,x
    cmp #4
    beq @up
    txa
    clc
    adc #1
    jsr try_group_neighbor
@up:
    ldx scan_index
    lda cell_rows,x
    beq @down
    txa
    sec
    sbc #5
    jsr try_group_neighbor
@down:
    ldx scan_index
    lda cell_rows,x
    cmp #4
    beq @loop
    txa
    clc
    adc #5
    jsr try_group_neighbor
    jmp @loop
@finished:
    lda queue_tail
    sta group_count
    rts

try_group_neighbor:
    tax
    lda visited,x
    bne @done
    lda board,x
    cmp group_value
    bne @done
    lda #1
    sta visited,x
    txa
    ldy queue_tail
    sta group_queue,y
    inc queue_tail
@done:
    rts

score_group:
    lda #0
    sta score_delta_lo
    sta score_delta_hi
    ldx group_count
@multiply:
    clc
    lda score_delta_lo
    adc group_value
    sta score_delta_lo
    bcc :+
    inc score_delta_hi
:
    dex
    bne @multiply
    lda group_value
    cmp #6
    bne @add
    clc
    lda score_delta_lo
    adc #50
    sta score_delta_lo
    bcc @add
    inc score_delta_hi
@add:
    clc
    lda score_lo
    adc score_delta_lo
    sta score_lo
    lda score_hi
    adc score_delta_hi
    sta score_hi
    bcc @done
    lda #$FF
    sta score_lo
    sta score_hi
@done:
    rts
