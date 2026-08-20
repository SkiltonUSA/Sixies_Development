.setcpu "6502"

.export _copy_buffer_to_aux
.export _replace_dhgr_sprite_aux
.export _replace_dhgr_sprite_main
.export _replace_dhgr_opaque_aux
.export _replace_dhgr_opaque_main
.export _clear_dhgr_tile_aux
.export _clear_dhgr_tile_main
.export _invert_dhgr_tile_aux
.export _invert_dhgr_tile_main
.export _draw_merge_effect_aux
.export _draw_merge_effect_main
.export _xor_merge_star
.import _dhgr_transfer_buffer
.import _dhgr_blit_source
.import _dhgr_blit_row_index
.import _dhgr_blit_row_end
.import _dhgr_blit_byte_offset
.import _dhgr_blit_byte_count
.import _dhgr_blit_last_byte
.import _dhgr_blit_first_mask
.import _dhgr_blit_last_mask
.import _dhgr_first_restore_source
.import _dhgr_last_restore_source
.import _dice_blit_row_low
.import _dice_blit_row_high
.import _merge_effect_row_low
.import _merge_effect_row_high
.import _merge_effect_byte_offset
.importzp ptr1, ptr2, ptr3, ptr4, tmp1, tmp2, tmp3

RAMWRT_MAIN = $C004
RAMWRT_AUX  = $C005
EIGHTY_STORE_OFF = $C000
EIGHTY_STORE_ON  = $C001
PAGE1 = $C054
PAGE2 = $C055
MERGE_EFFECT_ROW_BYTES = 20
MERGE_EFFECT_HEIGHT = 48
MERGE_STAR_ROW_BYTES = 8

.segment "CODE"

; void __fastcall__ copy_buffer_to_aux(void* destination)
; AX contains the auxiliary destination. Reads remain mapped to main memory, so
; the fixed 1 KB transfer buffer and executable stay visible during the copy.
.proc _copy_buffer_to_aux
    sta ptr1
    stx ptr1+1
    lda #<_dhgr_transfer_buffer
    sta ptr2
    lda #>_dhgr_transfer_buffer
    sta ptr2+1

    sta RAMWRT_AUX
    ldx #4
    ldy #0
copy_page:
    lda (ptr2),y
    sta (ptr1),y
    iny
    bne copy_page
    inc ptr1+1
    inc ptr2+1
    dex
    bne copy_page
    sta RAMWRT_MAIN
    rts
.endproc

; Clear one 24-row cell interior in the currently selected write bank. Edge
; masks preserve neighboring grid pixels while interior bytes become opaque.
.proc _clear_dhgr_tile_aux
    sta RAMWRT_AUX
    jsr clear_dhgr_tile
    sta RAMWRT_MAIN
    rts
.endproc

.proc _clear_dhgr_tile_main
    jmp clear_dhgr_tile
.endproc

clear_dhgr_tile:
    lda _dhgr_first_restore_source
    sta ptr3
    lda _dhgr_first_restore_source+1
    sta ptr3+1
    lda _dhgr_last_restore_source
    sta ptr4
    lda _dhgr_last_restore_source+1
    sta ptr4+1
    ldx _dhgr_blit_row_index

clear_row:
    ldy #0
    lda (ptr3),y
    sta tmp1
    lda (ptr4),y
    sta tmp2

    lda _dice_blit_row_low,x
    clc
    adc _dhgr_blit_byte_offset
    sta ptr2
    lda _dice_blit_row_high,x
    adc #0
    sta ptr2+1
    ldy #0

    lda tmp1
    sta (ptr2),y
    iny

clear_middle:
    cpy _dhgr_blit_last_byte
    beq clear_last
    lda #0
    sta (ptr2),y
    iny
    bne clear_middle

clear_last:
    lda tmp2
    sta (ptr2),y
    inc ptr3
    bne clear_first_ready
    inc ptr3+1
clear_first_ready:
    inc ptr4
    bne clear_last_ready
    inc ptr4+1
clear_last_ready:
    inx
    cpx _dhgr_blit_row_end
    bne clear_row
    rts

; Invert one 24-row cell interior for the monochrome merge ripple. Complete
; bytes flip their seven signal bits; edge masks preserve adjacent grid data.
.proc _invert_dhgr_tile_aux
    sta EIGHTY_STORE_ON
    sta PAGE2
    jsr invert_dhgr_tile
    sta EIGHTY_STORE_OFF
    sta PAGE1
    rts
.endproc

.proc _invert_dhgr_tile_main
    sta EIGHTY_STORE_OFF
    sta PAGE1
    sta RAMWRT_MAIN
    jmp invert_dhgr_tile
.endproc

invert_dhgr_tile:
    ldx _dhgr_blit_row_index

invert_tile_row:
    lda _dice_blit_row_low,x
    clc
    adc _dhgr_blit_byte_offset
    sta ptr2
    lda _dice_blit_row_high,x
    adc #0
    sta ptr2+1
    ldy #0

    lda (ptr2),y
    eor _dhgr_blit_first_mask
    sta (ptr2),y
    iny

invert_tile_middle:
    cpy _dhgr_blit_last_byte
    beq invert_tile_last
    lda (ptr2),y
    eor #$7F
    sta (ptr2),y
    iny
    bne invert_tile_middle

invert_tile_last:
    lda (ptr2),y
    eor _dhgr_blit_last_mask
    sta (ptr2),y
    inx
    cpx _dhgr_blit_row_end
    bne invert_tile_row
    rts

; Replace one full 24-row sprite plane in the selected bank. Edge masks retain
; grid pixels outside the cell; all sprite pixels and phase bits are opaque.
.proc _replace_dhgr_sprite_aux
    sta RAMWRT_AUX
    jsr replace_dhgr_sprite
    sta RAMWRT_MAIN
    rts
.endproc

.proc _replace_dhgr_sprite_main
    jmp replace_dhgr_sprite
.endproc

replace_dhgr_sprite:
    lda _dhgr_blit_source
    sta ptr1
    lda _dhgr_blit_source+1
    sta ptr1+1
    lda _dhgr_first_restore_source
    sta ptr3
    lda _dhgr_first_restore_source+1
    sta ptr3+1
    lda _dhgr_last_restore_source
    sta ptr4
    lda _dhgr_last_restore_source+1
    sta ptr4+1
    ldx _dhgr_blit_row_index

replace_row:
    ldy #0
    lda (ptr3),y
    sta tmp2
    lda (ptr4),y
    sta tmp3

    lda _dice_blit_row_low,x
    clc
    adc _dhgr_blit_byte_offset
    sta ptr2
    lda _dice_blit_row_high,x
    adc #0
    sta ptr2+1
    ldy #0

    lda (ptr1),y
    and _dhgr_blit_first_mask
    sta tmp1
    lda tmp2
    ora tmp1
    sta (ptr2),y
    iny

replace_middle:
    cpy _dhgr_blit_last_byte
    beq replace_last
    lda (ptr1),y
    sta (ptr2),y
    iny
    bne replace_middle

replace_last:
    lda (ptr1),y
    and _dhgr_blit_last_mask
    sta tmp1
    lda tmp3
    ora tmp1
    sta (ptr2),y

    clc
    lda ptr1
    adc #5
    sta ptr1
    bcc source_ready
    inc ptr1+1
source_ready:
    inc ptr3
    bne replace_first_ready
    inc ptr3+1
replace_first_ready:
    inc ptr4
    bne replace_last_ready
    inc ptr4+1
replace_last_ready:
    inx
    cpx _dhgr_blit_row_end
    bne replace_row
    rts

; Replace a fixed-position sprite against an already black panel. Unlike the
; board blitter, edge bits are preserved from screen memory instead of a grid
; restore table, allowing resident board sprite data to be reused in sidebar.
.proc _replace_dhgr_opaque_aux
    sta RAMWRT_AUX
    jsr replace_dhgr_opaque
    sta RAMWRT_MAIN
    rts
.endproc

.proc _replace_dhgr_opaque_main
    jmp replace_dhgr_opaque
.endproc

replace_dhgr_opaque:
    lda _dhgr_blit_source
    sta ptr1
    lda _dhgr_blit_source+1
    sta ptr1+1
    ldx _dhgr_blit_row_index

opaque_row:
    lda _dice_blit_row_low,x
    clc
    adc _dhgr_blit_byte_offset
    sta ptr2
    lda _dice_blit_row_high,x
    adc #0
    sta ptr2+1
    ldy #0

    lda _dhgr_blit_first_mask
    eor #$7F
    sta tmp1
    lda (ptr2),y
    and tmp1
    sta tmp2
    lda (ptr1),y
    and _dhgr_blit_first_mask
    ora tmp2
    sta (ptr2),y
    iny

opaque_middle:
    cpy _dhgr_blit_last_byte
    beq opaque_last
    lda (ptr1),y
    sta (ptr2),y
    iny
    bne opaque_middle

opaque_last:
    lda _dhgr_blit_last_mask
    eor #$7F
    sta tmp1
    lda (ptr2),y
    and tmp1
    sta tmp2
    lda (ptr1),y
    and _dhgr_blit_last_mask
    ora tmp2
    sta (ptr2),y

    clc
    lda ptr1
    adc #5
    sta ptr1
    bcc opaque_source_ready
    inc ptr1+1
opaque_source_ready:
    inx
    cpx _dhgr_blit_row_end
    bne opaque_row
    rts

.segment "LC"

; XOR one phase-aligned star at arbitrary DHGR coordinates. The source stores
; eight interleaved DHGR sequence bytes per active row; repeating the call
; restores every underlying signal exactly.
.proc _xor_merge_star
    lda _dhgr_blit_source
    sta ptr1
    lda _dhgr_blit_source+1
    sta ptr1+1
    lda #0
    sta tmp3

xor_star_row:
    ldx tmp3
    lda _merge_effect_row_low,x
    clc
    adc _dhgr_blit_byte_offset
    sta ptr2
    lda _merge_effect_row_high,x
    adc #0
    sta ptr2+1

    ldx #0
xor_star_byte:
    txa
    tay
    lda (ptr1),y
    sta tmp1

    txa
    clc
    adc _dhgr_blit_first_mask
    lsr
    sta tmp2

    txa
    and #1
    eor _dhgr_blit_first_mask
    beq xor_star_aux
    sta EIGHTY_STORE_OFF
    sta PAGE1
    sta RAMWRT_MAIN
    jmp xor_star_mapped
xor_star_aux:
    sta EIGHTY_STORE_ON
    sta PAGE2
xor_star_mapped:
    ldy tmp2
    lda (ptr2),y
    eor tmp1
    sta (ptr2),y

    inx
    cpx #MERGE_STAR_ROW_BYTES
    bne xor_star_byte

xor_star_next_row:
    clc
    lda ptr1
    adc #MERGE_STAR_ROW_BYTES
    sta ptr1
    bcc xor_star_source_ready
    inc ptr1+1
xor_star_source_ready:
    inc tmp3
    lda tmp3
    cmp _dhgr_blit_row_end
    bne xor_star_row

xor_star_done:
    sta EIGHTY_STORE_OFF
    sta PAGE1
    sta RAMWRT_MAIN
    rts
.endproc

.segment "CODE"

; Draw one opaque 960-byte effect plane. The generated data begins at signal
; pixel zero; a runtime byte offset positions its complete DHGR byte pairs.
.proc _draw_merge_effect_aux
    sta RAMWRT_AUX
    jsr draw_merge_effect
    sta RAMWRT_MAIN
    rts
.endproc

.proc _draw_merge_effect_main
    jmp draw_merge_effect
.endproc

draw_merge_effect:
    lda #<_dhgr_transfer_buffer
    sta ptr1
    lda #>_dhgr_transfer_buffer
    sta ptr1+1
    ldx #0

merge_effect_row:
    lda _merge_effect_row_low,x
    clc
    adc _merge_effect_byte_offset
    sta ptr2
    lda _merge_effect_row_high,x
    adc #0
    sta ptr2+1
    ldy #0

merge_effect_byte:
    lda (ptr1),y
    sta (ptr2),y
    iny
    cpy #MERGE_EFFECT_ROW_BYTES
    bne merge_effect_byte

    clc
    lda ptr1
    adc #MERGE_EFFECT_ROW_BYTES
    sta ptr1
    bcc merge_effect_source_ready
    inc ptr1+1
merge_effect_source_ready:
    inx
    cpx #MERGE_EFFECT_HEIGHT
    bne merge_effect_row
    rts
