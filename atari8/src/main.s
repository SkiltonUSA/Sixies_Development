.setcpu "6502"
.include "src/hardware.inc"

.segment "ZEROPAGE"
zp_screen:          .res 2
zp_asset:           .res 2
zp_text:            .res 2
zp_modulus:         .res 1
zp_target:          .res 1
zp_adjacent:        .res 1
zp_choice:          .res 1
zp_temp:            .res 1
zp_frames:          .res 1
zp_old_frame:       .res 1
; PORTB swaps the entire $4000-$7FFF CPU window on a 130XE. Keep the
; restoration state below that window so it remains visible while banked.
zp_saved_portb:     .res 1
zp_saved_main_4000: .res 1
zp_saved_main_4001: .res 1
zp_detected_kb:     .res 1

.segment "BSS"
ram_kb:             .res 1
input_latch:        .res 1
last_action:        .res 1
title_cached:       .res 1

.segment "CODE"
.export start

start:
    sei
    cld
    ldx #$FF
    txs
    lda #CH_NONE
    sta CH
    lda #0
    sta input_latch
    sta title_cached
    ; SEI does not mask ANTIC NMIs. Keep the OS VBI out of the $4000-$7FFF
    ; probe window until video_update_end installs the normal VBI state.
    sta NMIEN
    jsr detect_memory
    jsr sound_init
    jsr video_init
    cli
    jsr high_scores_init
.ifdef HIGH_SCORE_DEMO
    lda #<$0578                 ; 1400, one point above the seeded first place
    sta score_lo
    lda #>$0578
    sta score_hi
    jsr high_scores_after_game
@high_score_demo_wait:
    jmp @high_score_demo_wait
.endif
    jsr show_presents
    lda #90
    jsr wait_frames

title_loop:
    lda ram_kb
    cmp #128
    bne @draw_title
    lda title_cached
    beq @draw_title
    jsr restore_title_128
    jmp @title_ready
@draw_title:
    jsr show_title
    jsr cache_title_128
@title_ready:
    jsr arm_input
    jsr sound_start_music
    jsr wait_for_title
    jsr sound_stop_music
    jsr show_instructions
    jsr arm_input
    jsr wait_for_start

begin_game:
    jsr new_game
    jsr render_game

game_loop:
    lda game_over
    beq :+
    jmp game_finished
:
    jsr wait_action
    cmp #ACTION_LEFT
    beq move_left
    cmp #ACTION_RIGHT
    beq move_right
    cmp #ACTION_UP
    beq move_up
    cmp #ACTION_DOWN
    beq move_down
    cmp #ACTION_ROTATE
    beq rotate_piece
    cmp #ACTION_PLACE
    bne :+
    jmp place_piece
:
    cmp #ACTION_NEW
    bne :+
    jmp request_new_game
:
    cmp #ACTION_INFO
    bne :+
    jmp instructions
:
    cmp #ACTION_MUTE
    bne :+
    jmp toggle_audio
:
    cmp #ACTION_DEBUG_FILL
    bne :+
    jmp debug_game_over
:
    jmp game_loop

move_left:
    lda cursor_x
    beq @done
    jsr erase_piece_preview
    dec cursor_x
    jsr play_move_sound
    jsr draw_piece_preview
@done:
    jmp game_loop

move_right:
    lda cursor_x
    cmp #4
    beq @done
    jsr erase_piece_preview
    inc cursor_x
    jsr play_move_sound
    jsr draw_piece_preview
@done:
    jmp game_loop

move_up:
    lda cursor_y
    beq @done
    jsr erase_piece_preview
    dec cursor_y
    jsr play_move_sound
    jsr draw_piece_preview
@done:
    jmp game_loop

move_down:
    lda cursor_y
    cmp #4
    beq @done
    jsr erase_piece_preview
    inc cursor_y
    jsr play_move_sound
    jsr draw_piece_preview
@done:
    jmp game_loop

rotate_piece:
    lda piece_count
    cmp #2
    beq :+
    jmp game_loop
:
    jsr erase_piece_preview
    inc orientation
    lda orientation
    and #3
    sta orientation
    jsr play_rotate_sound
    jsr draw_piece_preview
    jmp game_loop

place_piece:
    jsr place_current_piece
    bcs :+
    jmp game_loop
:
    jsr play_place_sound
    jsr refresh_turn_display
    jmp game_loop

toggle_audio:
    jsr sound_toggle
    jmp game_loop

; Development shortcut: display a completely occupied board, then follow the
; same Game Over and high-score path as a naturally exhausted grid.
debug_game_over:
    jsr debug_fill_board
    jsr render_game
    jmp game_loop

instructions:
    jsr show_instructions
@wait:
    jsr wait_action
    cmp #ACTION_PLACE
    beq @return
    cmp #ACTION_INFO
    bne @wait
@return:
    jsr render_game
    jmp game_loop

request_new_game:
    jsr show_new_game_confirm
@confirm:
    jsr wait_action
    cmp #ACTION_YES
    bne :+
    jmp begin_game
:
    cmp #ACTION_NEW
    bne @confirm
    jsr render_game
    jmp game_loop

game_finished:
    jsr show_game_over
    jsr arm_input
    jsr wait_for_start
    jsr high_scores_after_game
    jsr arm_input
    jsr wait_for_start
    jmp begin_game

wait_for_start:
@wait:
    jsr wait_action
    cmp #ACTION_PLACE
    beq @done
    cmp #ACTION_NEW
    beq @done
    cmp #ACTION_YES
    bne @wait
@done:
    rts

; Require joystick/fire/console input to return to neutral before a title-screen
; press is accepted. Atari800 can briefly assert keyboard-joystick fire while
; its window is being created, which must not skip the title.
arm_input:
    lda #CH_NONE
    sta CH
    lda #1
    sta input_latch
    rts

; Returns an ACTION_* in A. Keyboard and joystick repeat only after neutral.
wait_action:
@poll:
    jsr sound_update
    lda #0
    sta ATRACT
    lda CONSOL
    and #1
    bne @keyboard
    lda input_latch
    bne @poll
    lda #1
    sta input_latch
    lda #ACTION_PLACE
    rts
@keyboard:
    lda CH
    cmp #CH_NONE
    beq @joystick
    sta zp_temp
    lda #CH_NONE
    sta CH
    ; Atari KBCODE stores Shift/Control in bits 6/7. Movement and action
    ; controls are physical keys, so shifted WASD should behave identically.
    lda zp_temp
    and #KEY_CODE_MASK
    sta zp_temp
    lda zp_temp
    cmp #KEY_A
    beq @left
    cmp #KEY_D
    beq @right
    cmp #KEY_W
    beq @up
    cmp #KEY_S
    beq @down
    cmp #KEY_Q
    beq @rotate
    cmp #KEY_E
    beq @rotate
    cmp #KEY_SPACE
    beq @place
    cmp #KEY_RETURN
    beq @place
    cmp #KEY_PERIOD
    beq @debug_fill
    cmp #KEY_C
    beq @credits
    cmp #KEY_N
    beq @new
    cmp #KEY_I
    beq @info
    cmp #KEY_M
    beq @mute
    cmp #KEY_Y
    beq @yes
    jmp @poll
@left:
    lda #ACTION_LEFT
    rts
@right:
    lda #ACTION_RIGHT
    rts
@up:
    lda #ACTION_UP
    rts
@down:
    lda #ACTION_DOWN
    rts
@rotate:
    lda #ACTION_ROTATE
    rts
@place:
    lda #ACTION_PLACE
    rts
@debug_fill:
    lda #ACTION_DEBUG_FILL
    rts
@credits:
    lda #ACTION_CREDITS
    rts
@new:
    lda #ACTION_NEW
    rts
@info:
    lda #ACTION_INFO
    rts
@mute:
    lda #ACTION_MUTE
    rts
@yes:
    lda #ACTION_YES
    rts
@joystick:
    ; Accept a physical/USB joystick on port 1 and Atari800's WASD keyboard
    ; joystick on port 2. This avoids SDL consuming WASD before it reaches CH.
    lda STICK0
    and #$0F
    sta zp_temp
    lda STRIG0
    beq @joy_fire
    lda zp_temp
    cmp #$0F
    bne @joy_direction
    lda STICK1
    and #$0F
    sta zp_temp
    lda STRIG1
    beq @joy_fire
    lda zp_temp
    cmp #$0F
    bne @joy_direction
    lda #0
    sta input_latch
    jmp @poll
@joy_fire:
    lda input_latch
    beq :+
    jmp @poll
:
    lda #1
    sta input_latch
    lda #ACTION_PLACE
    rts
@joy_direction:
    lda input_latch
    beq :+
    jmp @poll
:
    lda #1
    sta input_latch
    lda zp_temp
    cmp #$0B
    beq @left
    cmp #$07
    beq @right
    cmp #$0E
    beq @up
    cmp #$0D
    beq @down
    jmp @poll

; Detect independent 130XE banks through PORTB while preserving main RAM.
; The probe routine itself is deliberately linked at the beginning of CODE.
detect_memory:
    lda #64
    sta zp_detected_kb
    lda PORTB
    sta zp_saved_portb
    lda $4000
    sta zp_saved_main_4000
    lda $4001
    sta zp_saved_main_4001

    lda zp_saved_portb
    and #$E3
    sta PORTB                  ; CPU: extended bank 0, ANTIC: main
    lda #$55
    sta $4000
    lda #$AA
    sta $4001

    lda zp_saved_portb
    and #$E3
    ora #$04
    sta PORTB                  ; CPU: extended bank 1
    lda #$A5
    sta $4000
    lda #$5A
    sta $4001

    lda zp_saved_portb
    and #$E3
    sta PORTB
    lda $4000
    cmp #$55
    bne @restore
    lda $4001
    cmp #$AA
    bne @restore
    lda zp_saved_portb
    and #$E3
    ora #$04
    sta PORTB
    lda $4000
    cmp #$A5
    bne @restore
    lda $4001
    cmp #$5A
    bne @restore
    lda #128
    sta zp_detected_kb
@restore:
    lda zp_saved_portb
    sta PORTB
    lda zp_saved_main_4000
    sta $4000
    lda zp_saved_main_4001
    sta $4001
    lda zp_detected_kb
    sta ram_kb
    rts

; The 128K enhancement stores the 7.5K title page in extended bank 2.
cache_title_128:
    lda ram_kb
    cmp #128
    bne @done
    jsr video_update_begin
    sei
    lda PORTB
    sta zp_saved_portb
    and #$E3
    ora #$08
    sta PORTB
    jsr copy_screen_to_bank
    lda zp_saved_portb
    sta PORTB
    cli
    lda #1
    sta title_cached
    jsr video_update_end
@done:
    rts

restore_title_128:
    jsr video_update_begin
    sei
    lda PORTB
    sta zp_saved_portb
    and #$E3
    ora #$08
    sta PORTB
    jsr copy_bank_to_screen
    lda zp_saved_portb
    sta PORTB
    cli
    jmp video_update_end

copy_screen_to_bank:
    lda #<SCREEN
    sta zp_screen
    lda #>SCREEN
    sta zp_screen+1
    lda #<$4000
    sta zp_asset
    lda #>$4000
    sta zp_asset+1
    ldx #SCREEN_PHYSICAL_PAGES
    ldy #0
@copy:
    lda (zp_screen),y
    sta (zp_asset),y
    iny
    bne @copy
    inc zp_screen+1
    inc zp_asset+1
    dex
    bne @copy
    rts

copy_bank_to_screen:
    lda #<$4000
    sta zp_asset
    lda #>$4000
    sta zp_asset+1
    lda #<SCREEN
    sta zp_screen
    lda #>SCREEN
    sta zp_screen+1
    ldx #SCREEN_PHYSICAL_PAGES
    ldy #0
@copy:
    lda (zp_asset),y
    sta (zp_screen),y
    iny
    bne @copy
    inc zp_asset+1
    inc zp_screen+1
    dex
    bne @copy
    rts

.include "src/rules.s"
.include "src/sound.s"
.include "src/sid_music.s"
.include "src/high_scores.s"
.include "src/credits.s"
.include "src/graphics.s"
