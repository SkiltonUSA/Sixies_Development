; Reusable screen-fade bobs effect.
;
; Configure these symbols before !source if your target demo uses different
; VIC memory or zero-page pointers:
;   screenfadebobs_screen_base
;   screenfadebobs_color_base
;   screenfadebobs_d018
;   screenfadebobs_charset_base
;   screenfadebobs_dst_ptr
;   screenfadebobs_color_ptr
;   screenfadebobs_border_color
;   screenfadebobs_background_color
;   screenfadebobs_multi1_color
;   screenfadebobs_multi2_color
;   screenfadebobs_bob_color
;
; Call screenfadebobs_build_charset once after selecting the VIC bank.
; Then call screenfadebobs_init and screenfadebobs_update once per frame.

!ifndef screenfadebobs_screen_base { screenfadebobs_screen_base = $0400 }
!ifndef screenfadebobs_color_base { screenfadebobs_color_base = $d800 }
!ifndef screenfadebobs_d018 { screenfadebobs_d018 = $1c }
!ifndef screenfadebobs_charset_base { screenfadebobs_charset_base = $3000 }
!ifndef screenfadebobs_dst_ptr { screenfadebobs_dst_ptr = $f9 }
!ifndef screenfadebobs_color_ptr { screenfadebobs_color_ptr = $fb }
!ifndef screenfadebobs_border_color { screenfadebobs_border_color = $0e }
!ifndef screenfadebobs_background_color { screenfadebobs_background_color = $00 }
!ifndef screenfadebobs_multi1_color { screenfadebobs_multi1_color = $06 }
!ifndef screenfadebobs_multi2_color { screenfadebobs_multi2_color = $0e }
!ifndef screenfadebobs_bob_color { screenfadebobs_bob_color = $0e }

screenfadebobs_setup_screen:
    lda #$1b
    sta $d011
    lda #$18
    sta $d016
    lda #screenfadebobs_d018
    sta $d018
    lda #screenfadebobs_multi1_color
    sta $d022
    lda #screenfadebobs_multi2_color
    sta $d023
    lda #screenfadebobs_border_color
    sta $d020
    lda #screenfadebobs_background_color
    sta $d021
    lda #$00
    sta $d015
    rts

screenfadebobs_build_charset:
    lda #$00
    ldx #$00
screenfadebobs_clear_charset_pages:
    sta screenfadebobs_charset_base+$000,x
    sta screenfadebobs_charset_base+$100,x
    sta screenfadebobs_charset_base+$200,x
    sta screenfadebobs_charset_base+$300,x
    sta screenfadebobs_charset_base+$400,x
    sta screenfadebobs_charset_base+$500,x
    sta screenfadebobs_charset_base+$600,x
    sta screenfadebobs_charset_base+$700,x
    inx
    bne screenfadebobs_clear_charset_pages
    ldx #$00
screenfadebobs_copy_charset_data:
    lda screenfadebobs_charset_data,x
    sta screenfadebobs_charset_base,x
    inx
    cpx #64
    bne screenfadebobs_copy_charset_data
    rts

screenfadebobs_init:
    jsr screenfadebobs_setup_screen
    lda #screenfadebobs_bob_color
    jsr screenfadebobs_fill_color_ram
    lda #$00
    jsr screenfadebobs_fill_screen_char
    lda #$00
    sta screenfadebobs_unlock_counter
    sta screenfadebobs_unlock_index
    sta screenfadebobs_hold_counter
    ldx #19
screenfadebobs_reset_columns:
    lda #$00
    sta screenfadebobs_can_draw_column,x
    lda #$06
    sta screenfadebobs_frame_pointers,x
    dex
    bpl screenfadebobs_reset_columns
    rts

screenfadebobs_update:
    lda screenfadebobs_unlock_index
    cmp #20
    bcc screenfadebobs_unlock_phase
    inc screenfadebobs_hold_counter
    lda screenfadebobs_hold_counter
    cmp #30
    bcc screenfadebobs_draw_phase
    jmp screenfadebobs_init
screenfadebobs_unlock_phase:
    inc screenfadebobs_unlock_counter
    lda screenfadebobs_unlock_counter
    cmp #2
    bcc screenfadebobs_draw_phase
    lda #$00
    sta screenfadebobs_unlock_counter
    ldx screenfadebobs_unlock_index
    inc screenfadebobs_can_draw_column,x
    inc screenfadebobs_unlock_index
screenfadebobs_draw_phase:
    lda #$00
    sta screenfadebobs_col_index
screenfadebobs_draw_column_loop:
    ldx screenfadebobs_col_index
    lda screenfadebobs_can_draw_column,x
    beq screenfadebobs_next_column
    lda screenfadebobs_frame_pointers,x
    tay
    lda screenfadebobs_anim_sequence,y
    pha
    lda screenfadebobs_col_index
    asl
    sta screenfadebobs_temp_col
    pla
    jsr screenfadebobs_draw_column
    ldx screenfadebobs_col_index
    dec screenfadebobs_frame_pointers,x
    lda screenfadebobs_frame_pointers,x
    cmp #$ff
    bne screenfadebobs_next_column
    lda #$00
    sta screenfadebobs_can_draw_column,x
screenfadebobs_next_column:
    inc screenfadebobs_col_index
    lda screenfadebobs_col_index
    cmp #20
    bne screenfadebobs_draw_column_loop
    rts

screenfadebobs_draw_column:
    sta screenfadebobs_temp_char
    ldx #$00
screenfadebobs_draw_rows:
    lda screenfadebobs_row_screen_lo,x
    sta screenfadebobs_dst_ptr
    lda screenfadebobs_row_screen_hi,x
    sta screenfadebobs_dst_ptr + 1
    lda screenfadebobs_row_color_lo,x
    sta screenfadebobs_color_ptr
    lda screenfadebobs_row_color_hi,x
    sta screenfadebobs_color_ptr + 1
    ldy screenfadebobs_temp_col
    lda screenfadebobs_temp_char
    sta (screenfadebobs_dst_ptr),y
    iny
    sta (screenfadebobs_dst_ptr),y
    lda #screenfadebobs_bob_color
    dey
    sta (screenfadebobs_color_ptr),y
    iny
    sta (screenfadebobs_color_ptr),y
    inx
    inx
    cpx #24
    bne screenfadebobs_draw_rows
    rts

screenfadebobs_fill_color_ram:
    sta screenfadebobs_temp_color
    ldx #$00
screenfadebobs_fill_color_pages:
    lda screenfadebobs_temp_color
    sta screenfadebobs_color_base+$000,x
    sta screenfadebobs_color_base+$100,x
    sta screenfadebobs_color_base+$200,x
    inx
    bne screenfadebobs_fill_color_pages
    ldx #$00
screenfadebobs_fill_color_tail:
    lda screenfadebobs_temp_color
    sta screenfadebobs_color_base+$300,x
    inx
    cpx #$e8
    bne screenfadebobs_fill_color_tail
    rts

screenfadebobs_fill_screen_char:
    sta screenfadebobs_temp_char
    ldx #$00
screenfadebobs_fill_screen_pages:
    lda screenfadebobs_temp_char
    sta screenfadebobs_screen_base+$000,x
    sta screenfadebobs_screen_base+$100,x
    sta screenfadebobs_screen_base+$200,x
    inx
    bne screenfadebobs_fill_screen_pages
    ldx #$00
screenfadebobs_fill_screen_tail:
    lda screenfadebobs_temp_char
    sta screenfadebobs_screen_base+$300,x
    inx
    cpx #$e8
    bne screenfadebobs_fill_screen_tail
    rts

screenfadebobs_row_screen_lo:
!for r, 0, 24 { !byte <(screenfadebobs_screen_base + r * 40) }
screenfadebobs_row_screen_hi:
!for r, 0, 24 { !byte >(screenfadebobs_screen_base + r * 40) }
screenfadebobs_row_color_lo:
!for r, 0, 24 { !byte <(screenfadebobs_color_base + r * 40) }
screenfadebobs_row_color_hi:
!for r, 0, 24 { !byte >(screenfadebobs_color_base + r * 40) }

screenfadebobs_anim_sequence:
!byte 0,1,2,3,2,1,0

screenfadebobs_charset_data:
!byte $00,$00,$00,$00,$00,$00,$00,$00
!byte $00,$00,$00,$18,$18,$00,$00,$00
!byte $00,$18,$3c,$7e,$7e,$3c,$18,$00
!byte $18,$3c,$7e,$ff,$ff,$7e,$3c,$18
!byte $00,$00,$18,$3c,$3c,$18,$00,$00
!byte $00,$18,$7e,$ff,$ff,$7e,$18,$00
!byte $00,$00,$3c,$7e,$7e,$3c,$00,$00
!byte $18,$18,$3c,$7e,$7e,$3c,$18,$18

screenfadebobs_temp_col:
!byte $00
screenfadebobs_temp_char:
!byte $00
screenfadebobs_temp_color:
!byte $00
screenfadebobs_unlock_counter:
!byte $00
screenfadebobs_unlock_index:
!byte $00
screenfadebobs_col_index:
!byte $00
screenfadebobs_hold_counter:
!byte $00
screenfadebobs_can_draw_column:
!fill 20,0
screenfadebobs_frame_pointers:
!fill 20,0
