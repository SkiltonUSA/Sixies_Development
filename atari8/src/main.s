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
gameplay_input:     .res 1
joy_fire_state:     .res 1 ; 0=idle, 1=pending placement, 2=rotation consumed fire
queued_action:      .res 1 ; latest movement during an animation; never placement
reduced_flashing:   .res 1

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
    sta gameplay_input
    sta joy_fire_state
    sta queued_action
    sta reduced_flashing
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
    jsr show_title
@title_ready:
    jsr arm_input
    jsr sound_start_music
    jsr wait_for_title
    jsr sound_stop_music
    jsr show_instructions
    jsr arm_input
    jsr wait_for_start

begin_game:
    lda #1
    sta gameplay_input
    jsr arm_input
    jsr new_game
    ; Keep the first hovering piece hidden until the spiral restores its
    ; center cell. The right-sidebar next-piece dice still render normally.
    lda #0
    sta piece_visible
    jsr render_game
    jsr run_game_start_spiral
    lda #1
    sta piece_visible
    jsr draw_piece_preview

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
    bne :+
    jmp rotate_piece
:
    cmp #ACTION_ROTATE_BACK
    bne :+
    jmp rotate_piece_back
:
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
    cmp #ACTION_FLASH
    bne :+
    jsr toggle_flashing
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

rotate_piece_back:
    lda #3
    bne rotate_with_step
rotate_piece:
    lda #1
rotate_with_step:
    sta last_action
    lda piece_count
    cmp #2
    beq :+
    jmp game_loop
:
    jsr erase_piece_preview
    clc
    lda orientation
    adc last_action
    and #3
    sta orientation
    jsr play_rotate_sound
    jsr redraw_piece_sidebar
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
    lda #0
    sta gameplay_input
    jsr show_instructions
@wait:
    jsr wait_action
    cmp #ACTION_PLACE
    beq @return
    cmp #ACTION_INFO
    bne @wait
@return:
    lda #1
    sta gameplay_input
    jsr arm_input
    jsr render_game
    jmp game_loop

request_new_game:
    lda #0
    sta gameplay_input
    jsr arm_input
    jsr show_new_game_confirm
@confirm:
    jsr wait_action
    cmp #ACTION_PLACE
    beq @yes
    cmp #ACTION_YES
    bne :+
@yes:
    jmp begin_game
:
    cmp #ACTION_LEFT
    beq @cancel
    cmp #ACTION_NEW
    bne @confirm
@cancel:
    lda #1
    sta gameplay_input
    jsr arm_input
    jsr render_game
    jmp game_loop

game_finished:
    lda #0
    sta gameplay_input
    jsr show_game_over
    jsr arm_input
    jsr wait_for_start
    jsr high_scores_after_game
    jsr arm_input
    jsr wait_for_scores_start
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
    lda #0
    sta joy_fire_state
    sta queued_action
    lda #CH_NONE
    sta CH
    lda #1
    sta input_latch
    rts

.segment "LOGIC"

; Blocking consumer around the nonblocking input sampler. Animations may keep
; one movement/rotation, but never queue a placement across a board mutation.
wait_action:
    lda queued_action
    beq @poll
    pha
    lda #0
    sta queued_action
    pla
    rts
@poll:
    jsr sound_update
    jsr update_chain_reaction_sidebar
    jsr poll_action
    cmp #ACTION_NONE
    beq @poll
    rts

; Returns ACTION_NONE when idle; clobbers A/flags/zp_temp, preserves X/Y.
poll_action:
    lda #0
    sta ATRACT
    lda CONSOL
    and #1
    bne @keyboard
    lda input_latch
    bne @none
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
    beq @rotate_back
    cmp #KEY_E
    beq @rotate
    cmp #KEY_SPACE
    beq @place
    cmp #KEY_RETURN
    beq @place
.ifdef DEBUG_CONTROLS
    cmp #KEY_PERIOD
    beq @debug_fill
.endif
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
    cmp #KEY_F
    beq @flash
    cmp #KEY_R
    beq @retry
@none:
    lda #ACTION_NONE
    rts
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
@rotate_back:
    lda #ACTION_ROTATE_BACK
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
@flash:
    lda #ACTION_FLASH
    rts
@retry:
    lda #ACTION_RETRY
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
    bne @released
    lda STICK1
    and #$0F
    sta zp_temp
    lda STRIG1
    beq @joy_fire
@released:
    lda joy_fire_state
    beq @direction_or_neutral
    pha
    lda #0
    sta joy_fire_state
    lda #1
    sta input_latch
    pla
    cmp #1
    bne @none
    jmp @place
@direction_or_neutral:
    lda zp_temp
    cmp #$0F
    bne @joy_direction
    lda #0
    sta input_latch
    jmp @none
@joy_fire:
    lda gameplay_input
    beq @menu_fire
    lda joy_fire_state
    bne @held
    lda input_latch
    beq :+
    jmp @none
:
    lda #1
    sta joy_fire_state
@held:
    lda zp_temp
    cmp #$0F
    bne @chord
    lda #0
    sta input_latch
    jmp @none
@chord:
    lda input_latch
    beq :+
    jmp @none
:
    lda zp_temp
    cmp #$0B
    beq @rotate_left
    cmp #$07
    beq :+
    jmp @none
:
    lda #ACTION_ROTATE
    bne @consume
@rotate_left:
    lda #ACTION_ROTATE_BACK
@consume:
    pha
    lda #2
    sta joy_fire_state
    lda #1
    sta input_latch
    pla
    rts
@menu_fire:
    lda input_latch
    beq :+
    jmp @none
:
    lda #1
    sta input_latch
    jmp @place
@joy_direction:
    lda input_latch
    beq :+
    jmp @none
:
    lda #1
    sta input_latch
    lda zp_temp
    cmp #$0B
    bne :+
    jmp @left
:
    cmp #$07
    bne :+
    jmp @right
:
    cmp #$0E
    bne :+
    jmp @up
:
    cmp #$0D
    bne :+
    jmp @down
:
    jmp @none

toggle_flashing:
    lda reduced_flashing
    eor #1
    sta reduced_flashing
    rts

; Frame waits use this without touching any renderer/rules scratch. Settings
; apply immediately; the visible labels refresh at the end of the turn.
service_animation_input:
    lda gameplay_input
    beq @done
    lda zp_temp
    pha
    jsr poll_action
    cmp #ACTION_MUTE
    bne :+
    jsr sound_toggle
    jmp @restore
:
    cmp #ACTION_FLASH
    bne :+
    jsr toggle_flashing
    jmp @restore
:
    cmp #ACTION_ROTATE_BACK
    beq @queue
    cmp #ACTION_LEFT
    bcc @restore
    cmp #ACTION_PLACE
    bcs @restore
@queue:
    sta queued_action
@restore:
    pla
    sta zp_temp
@done:
    rts

.segment "CODE"

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

.include "src/rules.s"
.include "src/sound.s"
.include "src/sid_music.s"
.include "src/high_scores.s"
.include "src/credits.s"
.include "src/graphics.s"
.include "src/ui.s"
.include "src/effects.s"

; Bank-visible routines must never migrate into the switched $4000 window.
; ld65 MEMORY limits also reject overlap with framebuffer and OS ROM.
.import __CODE_RUN__, __CODE_SIZE__, __BSS_RUN__, __BSS_SIZE__
.assert __CODE_RUN__ + __CODE_SIZE__ <= $4000, lderror, "CODE crosses XE bank window"
.assert __BSS_RUN__ + __BSS_SIZE__ <= SCREEN, lderror, "State overlaps framebuffer"
.assert (display_list & $3FF) = 0, lderror, "Display list must be 1K aligned"
.assert sapr_wave4 + $100 <= $C000, lderror, "Music buffers overlap OS ROM"
.assert CALLOUT_UNDERLAY + 240 <= $A000, error, "Overlay overlaps high RAM"
