; POKEY translation of the C64/Apple II game cues. The pitch envelopes and
; musical intent are preserved; SID register data itself is not portable.

.segment "BSS"
sound_enabled:      .res 1
sound_frames:       .res 1
sound_mode:         .res 1
sound_pitch:        .res 1
music_enabled:      .res 1
music_divider:      .res 1
music_step:         .res 1

.segment "RODATA"
merge_pitch:        .byte $78,$64,$52,$43,$35,$28
title_notes:        .byte $60,$50,$43,$50,$3C,$32,$2A,$32,$48,$3C,$30,$3C,$28,$24,$20,$24

.segment "CODE"

sound_init:
    lda #3
    sta SKCTL
    lda #0
    sta AUDCTL
    sta AUDF1
    sta AUDF2
    sta AUDF3
    sta AUDF4
    sta AUDC1
    sta AUDC2
    sta AUDC3
    sta AUDC4
    sta sound_frames
    sta sound_mode
    sta music_divider
    sta music_step
    lda #1
    sta sound_enabled
    rts

sound_toggle:
    lda sound_enabled
    eor #1
    sta sound_enabled
    bne @done
    lda #0
    sta AUDC1
    sta AUDC2
    sta AUDC3
    sta AUDC4
@done:
    rts

play_move_sound:
    lda sound_enabled
    beq @done
    lda #$48
    sta AUDF1
    lda #$A6
    sta AUDC1
    lda #2
    sta sound_frames
    lda #1
    sta sound_mode
@done:
    rts

play_rotate_sound:
    lda sound_enabled
    beq @done
    lda #$34
    sta AUDF1
    lda #$A8
    sta AUDC1
    lda #4
    sta sound_frames
    lda #2
    sta sound_mode
@done:
    rts

play_place_sound:
    lda sound_enabled
    beq @done
    lda #$24
    sta AUDF1
    lda #$AA
    sta AUDC1
    lda #5
    sta sound_frames
    lda #3
    sta sound_mode
@done:
    rts

play_invalid_sound:
    lda sound_enabled
    beq @done
    lda #$38
    sta AUDF1
    sta sound_pitch
    lda #$C9
    sta AUDC1
    lda #10
    sta sound_frames
    lda #4
    sta sound_mode
@done:
    rts

; A = merged face value 1..6.
play_merge_sound:
    pha
    lda sound_enabled
    beq @muted
    pla
    sec
    sbc #1
    tax
    lda merge_pitch,x
    sta AUDF1
    sta sound_pitch
    lda #$AA
    sta AUDC1
    lda #16
    sta sound_frames
    lda #5
    sta sound_mode
    rts
@muted:
    pla
    rts

sound_update:
    lda sound_enabled
    beq @done
    lda sound_frames
    beq @music
    dec sound_frames
    beq @stop_effect
    lda sound_mode
    cmp #4
    beq @fall
    cmp #5
    beq @rise
    jmp @done
@fall:
    inc sound_pitch
    inc sound_pitch
    lda sound_pitch
    sta AUDF1
    jmp @done
@rise:
    lda sound_frames
    and #3
    bne @done
    lda sound_pitch
    sec
    sbc #7
    sta sound_pitch
    sta AUDF1
    jmp @done
@stop_effect:
    lda #0
    sta AUDC1
@music:
    lda music_enabled
    beq @done
    inc music_divider
    lda music_divider
    cmp #6
    bcc @done
    lda #0
    sta music_divider
    ldx music_step
    lda title_notes,x
    sta AUDF2
    lda #$A5
    sta AUDC2
    inx
    txa
    and #$0F
    sta music_step
@done:
    rts

sound_stop_music:
    lda #0
    sta music_enabled
    sta AUDC2
    rts
