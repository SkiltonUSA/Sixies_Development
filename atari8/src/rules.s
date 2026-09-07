; Platform-independent Sixies rules, implemented in 6502 assembly.
; This keeps the Apple IIe merge/scoring core, with the Atari progression
; requested for dealing pieces: 75% pairs and milestone-unlocked 4/5 pieces.
; Forced singles, complete orthogonal groups, origin-first double resolution,
; and the 50-point value-6 removal bonus remain unchanged.

CALLOUT_FRAMES = 30

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
rng_state:          .res 4
game_over:          .res 1
piece_visible:      .res 1
four_unlocked:      .res 1
five_unlocked:      .res 1
four_active:        .res 1
four_pressure:      .res 1
four_board_count:   .res 1
occupied_count:     .res 1
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
; Six opening ordered pairs. 1+1, 2+1, and 2+2 are deliberately absent.
; Index 6 (3+4) unlocks after merging 4+ fours; index 7 (4+5) unlocks after
; clearing 4+ sixes. Singles 4 and 5 use the same milestone flags.
pair_first:         .byte 1,1,2,3,3,3,3,4
pair_second:        .byte 2,3,3,1,2,3,4,5
; All unlocked pairs except 3+3. That pair has a fixed 1/15 share of pair
; deals (5% of normal turns); these choices divide the remaining 70%.
other_pair_index:   .byte 0,1,2,3,4,6,7
pressure_other_pair_index: .byte 0,1,2,3,4,7
four_pressure_singles:     .byte 1,2,3,3,4,4,4,4,4,4
four_pressure_singles_five:.byte 1,2,3,3,4,4,4,4,4,5
debug_full_board:   .byte 1,2,3,4,5, 2,3,4,5,6, 3,4,5,6,1
                    .byte 4,5,6,1,2, 5,6,1,2,3
; Match Apple II first_merge_effects: Awesome (0), Fives (3), and Sixies (5)
; are reserved and never selected for a first generic merge.
first_merge_callouts: .byte 1,2,4,6,7,8,9

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
    sta four_unlocked
    sta five_unlocked
    sta chain_banner_frames
    ; Seed the same four-byte generator used by cc65 rand() on Apple IIe.
    lda RTCLOK+2
    eor RANDOM
    sta rng_state
    sta rng_state+2
    lda RTCLOK+1
    eor RANDOM
    sta rng_state+1
    sta rng_state+3
    jsr random16
    jsr spawn_piece
    rts

; Fill all 25 cells with a merge-free Latin pattern for the period-key test
; shortcut. Unlike faces remain orthogonally adjacent, like a blocked game.
debug_fill_board:
    ldx #24
@fill:
    lda debug_full_board,x
    sta board,x
    dex
    bpl @fill
    lda #0
    sta piece_visible
    lda #1
    sta game_over
    rts

; cc65's 32-bit LCG (a=$01010101, c=$B3B3B3B3), matching the Apple IIe
; runtime. Return its 15-bit rand() result in X:A (high:low).
random16:
    clc
    lda rng_state
    adc #$B3
    sta rng_state
    adc rng_state+1
    sta rng_state+1
    adc rng_state+2
    sta rng_state+2
    eor rng_state
    and #$7F
    tax
    lda rng_state+2
    adc rng_state+3
    sta rng_state+3
    eor rng_state+1
    rts

; X = modulus (1..255), returns the complete 15-bit random value modulo X.
; Consuming both bytes prevents conditional correlations between the normal
; pair/single roll and the following face/pair roll. Z reflects returned A;
; the loop's final DEY must not leak its always-zero condition to callers.
random_mod_x:
    stx zp_modulus
    jsr random16
    sta zp_choice
    stx zp_temp
    lda #0
    ldy #16
@bit:
    asl zp_choice
    rol zp_temp
    rol
    cmp zp_modulus
    bcc @next
    sbc zp_modulus
@next:
    dey
    bne @bit
    cmp #0
    rts

; Measure density and the dynamic four-die pressure condition in one board
; scan. Clobbers A/X/flags; results are used only by the following spawn.
measure_board_pressure:
    lda #0
    sta occupied_count
    sta four_board_count
    ldx #0
@loop:
    lda board,x
    beq @next
    inc occupied_count
    cmp #4
    bne @next
    inc four_board_count
@next:
    inx
    cpx #25
    bne @loop
    lda #0
    ldx four_board_count
    cpx #4
    bcc :+
    lda #1
:
    sta four_pressure
    ora four_unlocked
    sta four_active
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
    jsr measure_board_pressure

    lda #3
    clc
    adc four_active
    adc five_unlocked
    sta eligible_count

    jsr has_adjacent_empty_pair
    sta zp_adjacent
    lda zp_adjacent
    beq @matching_single

    ; Density rescue progressively replaces ordinary deals with a useful
    ; matching single. 18..21 occupied cells: 50%; 22..24: 75%.
    lda occupied_count
    cmp #22
    bcc @medium_density
    ldx #4
    jsr random_mod_x
    beq @normal_deal
    jmp @matching_single
@medium_density:
    cmp #18
    bcc @normal_deal
    ldx #2
    jsr random_mod_x
    beq @matching_single

@normal_deal:
    ; Otherwise normal play is one single in four.
    ldx #4
    jsr random_mod_x
    beq @single

@pair:
    ldx #15
    jsr random_mod_x
    beq @double_three
    sta zp_choice
    lda four_pressure
    beq @normal_pair_pool
    lda zp_choice
    cmp #8
    bcc @pressure_four_pair
    lda #5
    clc
    adc five_unlocked
    tax
    jsr random_mod_x
    tax
    lda pressure_other_pair_index,x
    tax
    bpl @store_pair
@pressure_four_pair:
    ldx #6
    bpl @store_pair
@normal_pair_pool:
    lda #5
    clc
    adc four_unlocked
    adc five_unlocked
    tax
    jsr random_mod_x
    tax
    lda other_pair_index,x
    tax
    bpl @store_pair
@double_three:
    ldx #5
@store_pair:
    lda #2
    sta piece_count
    lda pair_first,x
    sta piece_a
    lda pair_second,x
    sta piece_b
    jmp @position

@matching_single:
    lda #1
    sta piece_count
    lda #0
    sta piece_b
    jsr weighted_surrounding_face
    bne @store_single
    ; No eligible neighboring face: fall back to the current single pool.
    jmp @normal_single

@single:
    lda #1
    sta piece_count
    lda #0
    sta piece_b
@normal_single:
    lda four_pressure
    beq @uniform_single
    ldx #10
    jsr random_mod_x
    tax
    lda five_unlocked
    beq @pressure_without_five
    lda four_pressure_singles_five,x
    bne @store_single
@pressure_without_five:
    lda four_pressure_singles,x
    bne @store_single
@uniform_single:
    ldx eligible_count
    jsr random_mod_x
    tax
    cpx #3
    bcc @base_single
    lda four_active
    beq @single_five
    cpx #3
    beq @single_four
@single_five:
    lda #5
    bne @store_single
@single_four:
    lda #4
    bne @store_single
@base_single:
    txa
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
    lda four_active
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
    jsr update_piece_unlocks
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
    jsr present_merge
    ldx active_index
    lda board,x
    beq @done
    jmp @again
@done:
    rts

; Unlocks are event milestones and remain set until new_game. A face may exist
; through ordinary merging before it becomes eligible to be dealt. Inputs are
; group_value/group_count from find_group; clobbers A/flags, preserves X/Y.
update_piece_unlocks:
    lda group_count
    cmp #4
    bcc @done
    lda group_value
    cmp #4
    bne :+
    lda #1
    sta four_unlocked
    rts
:
    cmp #6
    bne @done
    lda #1
    sta five_unlocked
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
    ; Apply one multiplier across the complete placement resolution, including
    ; an origin merge followed by the partner die. merge_depth is incremented
    ; before this call: first x1, second x2, third x3, and so forth. The six
    ; clear bonus is part of the multiplied award. Arithmetic wraps at 16 bits.
    lda score_delta_lo
    sta zp_choice
    lda score_delta_hi
    sta zp_temp
    lda #0
    sta score_delta_lo
    sta score_delta_hi
    ldx merge_depth
    bne @chain_add
    ldx #1                    ; Safe default for direct diagnostic calls.
@chain_add:
    clc
    lda score_delta_lo
    adc zp_choice
    sta score_delta_lo
    lda score_delta_hi
    adc zp_temp
    sta score_delta_hi
    dex
    bne @chain_add

    clc
    lda score_lo
    adc score_delta_lo
    sta score_lo
    lda score_hi
    adc score_delta_hi
    sta score_hi
    ; cc65 unsigned int scores on Apple IIe wrap naturally at 16 bits.
    rts
