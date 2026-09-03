; ---------------------------------------------------------------------------
; sid_music.s -- compressed SID2SAPR softbass title-music player.
;
; The C64 SID was converted offline with ivop/saprtools sid2sapr 1.11:
;
;   sid2sapr -b softbass -a -p 9 -n 961 ...
;   lzss -6 input.sapr output.lz16
;
; The register stream and conversion are BSD-2-Clause (Ivo van Poorten).
; This ca65 LZSS/softbass adaptation follows the MIT-licensed DMSC player
; shipped with saprtools. While timer-driven bass is active, title input polls
; POKEY directly; the OS IRQ vector and mask are restored before gameplay.
;
; The source tune is PAL/50 Hz. Sixies runs NTSC/60 Hz, so sid_music_tick
; advances five out of every six display frames. The complete compressed tune
; restarts if the player remains on the title screen past its end.
; ---------------------------------------------------------------------------

.segment "ZEROPAGE"
sapr_bptr:             .res 2

.segment "BSS"
sapr_active:           .res 1
sapr_last_frame:       .res 1
sapr_ratediv:          .res 1
sapr_cur_pos:          .res 1
sapr_chn_bits:         .res 1
sapr_bit_data:         .res 1
sapr_chn_copy:         .res 9
sapr_chn_pos:          .res 9
sapr_shadow:           .res 9
sapr_saved_pokmsk:     .res 1
sapr_saved_vimirq:     .res 2

SAPR_SAUDF1  = sapr_shadow + 0
SAPR_SAUDC1  = sapr_shadow + 1
SAPR_SAUDF2  = sapr_shadow + 2
SAPR_SAUDC2  = sapr_shadow + 3
SAPR_SAUDF3  = sapr_shadow + 4
SAPR_SAUDC3  = sapr_shadow + 5
SAPR_SAUDF4  = sapr_shadow + 6
SAPR_SAUDC4  = sapr_shadow + 7
SAPR_SAUDCTL = sapr_shadow + 8

SAPR_ENA1 = $01
SAPR_ENA2 = $02
SAPR_ENA4 = $04
SAPR_DIS1 = $FE
SAPR_DIS2 = $FD
SAPR_DIS4 = $FB
SAPR_DISTIMERS = $F8

.segment "MUSICCODE"

; Start playback and install the timer-only IRQ used by softbass. The original
; saprtools player disables OS POKEY IRQ sources while its high-rate timers are
; active; doing the same prevents timer interrupts from nesting inside the OS
; keyboard handler and exhausting the 6502 stack during a long attract loop.
sid_music_start:
    lda #3
    sta SSKCTL
    sta SKCTL

    php
    sei
    lda POKMSK
    sta sapr_saved_pokmsk
    lda #0
    sta POKMSK
    sta IRQEN
    lda VIMIRQ
    sta sapr_saved_vimirq
    lda VIMIRQ+1
    sta sapr_saved_vimirq+1
    lda #<sapr_irq
    sta VIMIRQ
    lda #>sapr_irq
    sta VIMIRQ+1
    plp

    jsr sapr_init_waves
    jsr sapr_reset_decoder
    jsr sapr_copy_shadow
    lda RTCLOK+2
    sta sapr_last_frame
    lda #0
    sta sapr_ratediv
    lda #1
    sta sapr_active
    rts

; Stop every music channel and return both the IRQ vector and POKEY interrupt
; mask to exactly the state they had before the title music started.
sid_music_stop:
    lda #0
    sta sapr_active
    php
    sei
    lda POKMSK
    and #SAPR_DISTIMERS
    sta POKMSK
    sta IRQEN
    lda sapr_saved_vimirq
    sta VIMIRQ
    lda sapr_saved_vimirq+1
    sta VIMIRQ+1
    lda sapr_saved_pokmsk
    sta POKMSK
    sta IRQEN
    plp

    lda #0
    sta AUDC1
    sta AUDC2
    sta AUDC3
    sta AUDC4
    sta AUDCTL
    rts

; Called from the title input loop. RTCLOK prevents multiple updates in one
; display frame; skipping each sixth NTSC frame gives the source's 50 Hz rate.
sid_music_tick:
    lda sapr_active
    beq @done
    lda RTCLOK+2
    cmp sapr_last_frame
    beq @done
    sta sapr_last_frame
    inc sapr_ratediv
    lda sapr_ratediv
    cmp #6
    bcc @play
    lda #0
    sta sapr_ratediv
    rts

@play:
    jsr sapr_decode_frame
    jsr sapr_copy_shadow
    lda sapr_get_byte_operand+1
    cmp #>sapr_song_end
    bcc @done
    bne @restart
    lda sapr_get_byte_operand
    cmp #<sapr_song_end
    bcc @done
@restart:
    jsr sapr_reset_decoder
@done:
    rts

; Initialize the eight-byte volume-only waveforms used for one- and two-octave
; software bass. Each waveform occupies its own aligned page because the IRQ
; advances through it by changing the low byte of an absolute LDA operand.
sapr_init_waves:
    ldx #7
@copy:
    lda sapr_wave_template,x
    sta sapr_wave1,x
    sta sapr_wave2,x
    sta sapr_wave4,x
    dex
    bpl @copy
    lda #<sapr_wave1
    sta sapr_irq_wave1_operand
    lda #<sapr_wave2
    sta sapr_irq_wave2_operand
    lda #<sapr_wave4
    sta sapr_irq_wave4_operand
    lda #3
    sta sapr_irq_oct1_operand
    sta sapr_irq_oct2_operand
    sta sapr_irq_oct4_operand
    rts

sapr_wave_template:
    .byte $1C,$1C,$10,$10,$10,$10,$1C,$1C

; Reset the LZSS state and read the nine initial POKEY register values. The
; first compressed byte is a static mask identifying registers that never
; change; byte fetching begins immediately after that mask.
sapr_reset_decoder:
    php
    sei
    lda POKMSK
    and #SAPR_DISTIMERS
    sta POKMSK
    sta IRQEN

    lda #<(sapr_song_data+1)
    sta sapr_get_byte_operand
    lda #>(sapr_song_data+1)
    sta sapr_get_byte_operand+1
    lda #1
    sta sapr_bit_data
    lda #0
    sta sapr_cur_pos
    lda #<(sapr_buffers+$FF)
    sta sapr_bptr
    lda #>sapr_buffers
    sta sapr_bptr+1
    ldx #8
    ldy #0
@initial:
    lda #0
    sta sapr_chn_copy,x
    sta sapr_chn_pos,x
    jsr sapr_get_byte
    sta sapr_shadow,x
    sta (sapr_bptr),y
    inc sapr_bptr+1
    dex
    bpl @initial
    plp
    rts

; Self-modifying byte fetch is substantially cheaper than preserving Y around
; an indirect load. The two operand bytes also form the decoder end pointer.
sapr_get_byte:
sapr_get_byte_operand = * + 1
    lda sapr_song_data+1
    inc sapr_get_byte_operand
    bne :+
    inc sapr_get_byte_operand+1
:
    rts

; Decode one frame. Each changing POKEY register has an independent 256-byte
; history page, matching saprtools' 16-bit LZSS stream format.
sapr_decode_frame:
    lda #<sapr_buffers
    sta sapr_bptr
    lda #>sapr_buffers
    sta sapr_bptr+1
    lda sapr_song_data
    sta sapr_chn_bits
    ldx #8
@channel:
    lsr sapr_chn_bits
    bcs @skip
    lda sapr_chn_copy,x
    bne @copy_byte
    lsr sapr_bit_data
    bne @have_bit
    jsr sapr_get_byte
    ror
    sta sapr_bit_data
@have_bit:
    jsr sapr_get_byte
    bcs @store
    sta sapr_chn_pos,x
    jsr sapr_get_byte
    sta sapr_chn_copy,x
@copy_byte:
    dec sapr_chn_copy,x
    inc sapr_chn_pos,x
    ldy sapr_chn_pos,x
    lda (sapr_bptr),y
@store:
    ldy sapr_cur_pos
    sta sapr_shadow,x
    sta (sapr_bptr),y
@skip:
    inc sapr_bptr+1
    dex
    bpl @channel
    inc sapr_cur_pos
    rts

; Update one softbass-capable channel from the decompressed shadow registers.
.macro SAPR_HANDLE_CHANNEL shadow_freq, shadow_ctrl, hw_freq, hw_ctrl, wave, oct_operand, enable_mask, disable_mask
    .local normal, frequency
    lda shadow_ctrl
    tay
    and #$10
    beq normal
    tya
    sta wave+0
    sta wave+1
    sta wave+6
    sta wave+7
    lsr
    lsr
    lsr
    lsr
    sta oct_operand
    lda POKMSK
    ora #enable_mask
    sta POKMSK
    sta IRQEN
    bne frequency
normal:
    lda POKMSK
    and #disable_mask
    sta POKMSK
    sta IRQEN
    tya
    sta hw_ctrl
frequency:
    lda shadow_freq
    sta hw_freq
.endmacro

sapr_copy_shadow:
    lda SAPR_SAUDCTL
    sta AUDCTL
    lda SAPR_SAUDC3
    sta AUDC3
    lda SAPR_SAUDF3
    sta AUDF3
    SAPR_HANDLE_CHANNEL SAPR_SAUDF1, SAPR_SAUDC1, AUDF1, AUDC1, sapr_wave1, sapr_irq_oct1_operand, SAPR_ENA1, SAPR_DIS1
    SAPR_HANDLE_CHANNEL SAPR_SAUDF2, SAPR_SAUDC2, AUDF2, AUDC2, sapr_wave2, sapr_irq_oct2_operand, SAPR_ENA2, SAPR_DIS2
    SAPR_HANDLE_CHANNEL SAPR_SAUDF4, SAPR_SAUDC4, AUDF4, AUDC4, sapr_wave4, sapr_irq_oct4_operand, SAPR_ENA4, SAPR_DIS4
    rts

; POKEY timer IRQs generate the volume-only softbass waveforms. Only timer
; sources are enabled during playback, matching saprtools' original handler.
sapr_irq:
    pha
    lda IRQST
    lsr
    bcc sapr_irq_timer1
    lsr
    bcc sapr_irq_timer2
    jmp sapr_irq_timer4

sapr_irq_timer1:
    lda POKMSK
    and #SAPR_DIS1
    sta IRQEN
    lda POKMSK
    sta IRQEN
sapr_irq_wave1_operand = * + 1
    lda sapr_wave1
    sta AUDC1
    dec sapr_irq_wave1_operand
    bpl sapr_irq_timer1_done
sapr_irq_oct1_operand = * + 1
    lda #3
    sta sapr_irq_wave1_operand
sapr_irq_timer1_done:
    pla
    rti

sapr_irq_timer2:
    lda POKMSK
    and #SAPR_DIS2
    sta IRQEN
    lda POKMSK
    sta IRQEN
sapr_irq_wave2_operand = * + 1
    lda sapr_wave2
    sta AUDC2
    dec sapr_irq_wave2_operand
    bpl sapr_irq_timer2_done
sapr_irq_oct2_operand = * + 1
    lda #3
    sta sapr_irq_wave2_operand
sapr_irq_timer2_done:
    pla
    rti

sapr_irq_timer4:
    lda POKMSK
    and #SAPR_DIS4
    sta IRQEN
    lda POKMSK
    sta IRQEN
sapr_irq_wave4_operand = * + 1
    lda sapr_wave4
    sta AUDC4
    dec sapr_irq_wave4_operand
    bpl sapr_irq_timer4_done
sapr_irq_oct4_operand = * + 1
    lda #3
    sta sapr_irq_wave4_operand
sapr_irq_timer4_done:
    pla
    rti

.segment "MUSIC"
sapr_song_data:
    .incbin "assets/music/eternity_1_intro_softbass.lz16"
sapr_song_end:

; Decoder history and wave pages occupy RAM but add nothing to the XEX file.
.segment "MUSICBSS"
.align $100
sapr_buffers:          .res $900
.align $100
sapr_wave1:            .res $100
sapr_wave2:            .res $100
sapr_wave4:            .res $100
