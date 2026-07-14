; "Galway Nights" player core -- original tune in the style of Martin Galway.
; Included by src/music/galway_nights.a (standalone PRG/PSID wrapper) and by
; src/main.a (demo soundtrack). Position independent apart from its own
; labels: call galway_init once, then galway_play every PAL frame.
; scripts/generate_galway_sid.py supplies the looping note streams.
;
; Voice 1: pulse lead with swept width and delayed, blooming vibrato.
; Voice 2: dotted-eighth echo of the lead at a quieter sustain level.
; Voice 3: bouncy octave pulse bass time-shared with pitch-drop kick and
;          noise snare, low-pass filtered with a slow cutoff sweep.

GALWAY_SNARE_PITCH = 125
GALWAY_KICK_PITCH = 126
GALWAY_LEAD_AGE_MAX = $3f

galway_frame_lo = $f7
galway_frame_hi = $f8
galway_event = $f9
galway_vib_index = $fa

galway_init:
    lda #$00
    sta galway_frame_lo
    sta galway_frame_hi
    sta galway_lead_age
    sta galway_lead_freq_lo
    sta galway_lead_freq_hi
    sta galway_kick_age
    sta galway_pw_dir

    ldx #$18
galway_clear_sid:
    sta $d400,x
    dex
    bpl galway_clear_sid

    lda #$40
    sta galway_lead_gate
    lda #$41
    sta galway_bass_wave

    ; Lead pulse width starts mid-sweep; the echo keeps a fixed thinner
    ; pulse so the delayed repeat sits behind the live note.
    lda #$00
    sta galway_pw_lo
    sta $d402
    sta $d409
    sta $d410
    lda #$08
    sta galway_pw_hi
    sta $d403
    lda #$05
    sta $d40a
    lda #$04
    sta $d411

    lda #$09                    ; singing lead: fast attack, high sustain
    sta $d405
    lda #$c6
    sta $d406
    lda #$09                    ; echo: same shape at half the level
    sta $d40c
    lda #$56
    sta $d40d
    lda #$05                    ; punchy pulse bass
    sta $d413
    lda #$a5
    sta $d414

    lda #$a4                    ; resonance 10, voice 3 through the filter
    sta $d417
    lda #$1f                    ; low-pass, full master volume
    sta $d418
    rts

galway_play:
    lda galway_frame_hi
    cmp #>GALWAY_LOOP_FRAMES
    bcc galway_render_frame
    bne galway_restart_sequence
    lda galway_frame_lo
    cmp #<GALWAY_LOOP_FRAMES
    bcc galway_render_frame

galway_restart_sequence:
    lda #$00
    sta galway_frame_lo
    sta galway_frame_hi
    jmp galway_render_frame
galway_play_done:
    rts

galway_render_frame:
    lda galway_frame_lo
    clc
    adc #<galway_lead_frames
    sta galway_lead_read+1
    lda galway_frame_hi
    adc #>galway_lead_frames
    sta galway_lead_read+2
galway_lead_read:
    lda galway_lead_frames
    jsr galway_update_lead

    lda galway_frame_lo
    clc
    adc #<galway_echo_frames
    sta galway_echo_read+1
    lda galway_frame_hi
    adc #>galway_echo_frames
    sta galway_echo_read+2
galway_echo_read:
    lda galway_echo_frames
    jsr galway_update_echo

    lda galway_frame_lo
    clc
    adc #<galway_bass_frames
    sta galway_bass_read+1
    lda galway_frame_hi
    adc #>galway_bass_frames
    sta galway_bass_read+2
galway_bass_read:
    lda galway_bass_frames
    jsr galway_update_bass
    jsr galway_update_effects

    inc galway_frame_lo
    bne galway_play_done
    inc galway_frame_hi
    rts

galway_update_lead:
    sta galway_event
    bne galway_lead_has_event
    lda #$40
    sta $d404
    sta galway_lead_gate
    rts
galway_lead_has_event:
    and #$7f
    tay
    lda sid_freq_lo,y
    sta galway_lead_freq_lo
    lda sid_freq_hi,y
    sta galway_lead_freq_hi
    lda galway_event
    bmi galway_lead_restart
    lda galway_lead_gate
    cmp #$41
    beq galway_lead_hold
    lda #$41                    ; open the gate; vibrato starts from zero
    sta $d404
    sta galway_lead_gate
    lda #$00
    sta galway_lead_age
    rts
galway_lead_hold:
    inc galway_lead_age         ; age drives the delayed vibrato bloom
    lda galway_lead_age
    cmp #GALWAY_LEAD_AGE_MAX
    bcc galway_lead_done
    lda #GALWAY_LEAD_AGE_MAX
    sta galway_lead_age
galway_lead_done:
    rts
galway_lead_restart:
    lda #$40                    ; one-frame hard restart before the note
    sta $d404
    sta galway_lead_gate
    lda #$00
    sta galway_lead_age
    rts

galway_update_echo:
    sta galway_event
    bne galway_echo_has_event
    lda #$40
    sta $d40b
    rts
galway_echo_has_event:
    and #$7f
    tay
    lda sid_freq_lo,y
    sta $d407
    lda sid_freq_hi,y
    sta $d408
    lda galway_event
    bmi galway_echo_restart
    lda #$41
    sta $d40b
    rts
galway_echo_restart:
    lda #$40
    sta $d40b
    rts

galway_update_bass:
    sta galway_event
    bne galway_bass_has_event
    lda galway_bass_wave        ; drop the gate on whatever wave is playing
    and #$fe
    sta $d412
    rts
galway_bass_has_event:
    and #$7f
    cmp #GALWAY_SNARE_PITCH
    beq galway_bass_snare
    cmp #GALWAY_KICK_PITCH
    beq galway_bass_kick
    tay
    lda sid_freq_lo,y
    sta $d40e
    lda sid_freq_hi,y
    sta $d40f
    lda galway_event
    bmi galway_bass_restart
    lda #$41
    sta $d412
    sta galway_bass_wave
    rts
galway_bass_restart:
    lda #$40
    sta $d412
    sta galway_bass_wave
    lda #$05                    ; restore the bass envelope after drums
    sta $d413
    lda #$a5
    sta $d414
    lda #$00
    sta galway_kick_age
    rts

galway_bass_snare:
    lda galway_event
    bmi galway_snare_restart
    lda #$81
    sta $d412
    sta galway_bass_wave
    rts
galway_snare_restart:
    lda #$80
    sta $d412
    sta galway_bass_wave
    lda #$06                    ; short bright noise burst
    sta $d413
    lda #$06
    sta $d414
    lda #$00
    sta $d40e
    sta galway_kick_age
    lda #$38                    ; bright pitched SID noise
    sta $d40f
    rts

galway_bass_kick:
    lda galway_event
    bmi galway_kick_restart
    lda #$11
    sta $d412
    sta galway_bass_wave
    rts
galway_kick_restart:
    lda #$10
    sta $d412
    sta galway_bass_wave
    lda #$09                    ; fast triangle thud, no sustain
    sta $d413
    lda #$00
    sta $d414
    lda #$04
    sta galway_kick_age
    rts

galway_update_effects:
    ; Galway-style pulse width sweep on the lead, reflecting between
    ; $0400 and $0c00 (roughly a one-second cycle).
    lda galway_pw_dir
    bne galway_pw_down
    lda galway_pw_lo
    clc
    adc #$30
    sta galway_pw_lo
    lda galway_pw_hi
    adc #$00
    sta galway_pw_hi
    cmp #$0c
    bcc galway_pw_write
    lda #$01
    sta galway_pw_dir
    bne galway_pw_write
galway_pw_down:
    lda galway_pw_lo
    sec
    sbc #$30
    sta galway_pw_lo
    lda galway_pw_hi
    sbc #$00
    sta galway_pw_hi
    cmp #$04
    bcs galway_pw_write
    lda #$00
    sta galway_pw_dir
galway_pw_write:
    lda galway_pw_lo
    sta $d402
    lda galway_pw_hi
    sta $d403

    ; Kick drum: the triangle pitch falls over four frames.
    lda galway_kick_age
    beq galway_kick_done
    tax
    lda galway_kick_freq_lo,x
    sta $d40e
    lda galway_kick_freq_hi,x
    sta $d40f
    dec galway_kick_age
galway_kick_done:

    ; Slow low-pass wah under the bass and drums.
    lda galway_frame_lo
    lsr
    lsr
    and #$1f
    tax
    lda galway_filter_cutoff,x
    sta $d416

    ; Delayed vibrato: silent for the first fifth of a second of a note,
    ; then blooming through three depth steps -- the Galway signature.
    lda galway_lead_gate
    cmp #$41
    bne galway_effects_done
    ldx galway_lead_age
    lda galway_vib_depth,x      ; depth row, pre-multiplied by 16
    sta galway_vib_index
    lda galway_frame_lo
    asl                         ; 8-frame period = 6.25 Hz wobble
    and #$0f
    ora galway_vib_index
    tay
    lda galway_vib_wave,y
    bmi galway_vib_negative
    clc
    adc galway_lead_freq_lo
    sta $d400
    lda galway_lead_freq_hi
    adc #$00
    sta $d401
    rts
galway_vib_negative:
    clc
    adc galway_lead_freq_lo
    sta $d400
    lda galway_lead_freq_hi
    adc #$ff
    sta $d401
galway_effects_done:
    rts

; Depth row (x16) by note age: a fifth of a second flat, then a fast
; bloom through shallow and medium to a full, deep wobble.
galway_vib_depth:
    !byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    !byte $10,$10,$10,$10,$10,$10
    !byte $20,$20,$20,$20,$20,$20
    !byte $30,$30,$30,$30,$30,$30,$30,$30,$30,$30,$30,$30,$30,$30,$30,$30
    !byte $30,$30,$30,$30,$30,$30,$30,$30,$30,$30,$30,$30,$30,$30,$30,$30
    !byte $30,$30,$30,$30,$30,$30,$30,$30,$30,$30

; Four 16-entry signed sine rows at increasing depth.
galway_vib_wave:
    !byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
    !byte 0,15,28,37,40,37,28,15,0,-15,-28,-37,-40,-37,-28,-15
    !byte 0,31,57,74,80,74,57,31,0,-31,-57,-74,-80,-74,-57,-31
    !byte 0,49,90,117,127,117,90,49,0,-49,-90,-117,-127,-117,-90,-49

; 32-entry triangle sweep for the low-pass cutoff.
galway_filter_cutoff:
    !byte $2a,$30,$36,$3c,$42,$48,$4e,$54,$5a,$60,$66,$6c,$72,$78,$7e,$84
    !byte $8a,$84,$7e,$78,$72,$6c,$66,$60,$5a,$54,$4e,$48,$42,$3c,$36,$30

; Kick pitch drop indexed by kick_age (4 down to 1, landing near 35 Hz).
galway_kick_freq_lo:
    !byte $80,$80,$30,$50,$00
galway_kick_freq_hi:
    !byte $02,$02,$03,$04,$08

galway_lead_age:
    !byte 0
galway_lead_freq_lo:
    !byte 0
galway_lead_freq_hi:
    !byte 0
galway_lead_gate:
    !byte 0
galway_bass_wave:
    !byte 0
galway_kick_age:
    !byte 0
galway_pw_lo:
    !byte 0
galway_pw_hi:
    !byte 0
galway_pw_dir:
    !byte 0

!source "src/generated/sid_pal_freq.inc"

; The three per-voice streams pack back to back so the loop length can
; change freely in the generator without touching any addresses.
galway_lead_frames:
!bin "src/music/galway_nights_frames.bin", GALWAY_LOOP_FRAMES, 0

galway_echo_frames:
!bin "src/music/galway_nights_frames.bin", GALWAY_LOOP_FRAMES, GALWAY_LOOP_FRAMES

galway_bass_frames:
!bin "src/music/galway_nights_frames.bin", GALWAY_LOOP_FRAMES, GALWAY_LOOP_FRAMES * 2
