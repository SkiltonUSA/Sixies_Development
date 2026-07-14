; One 48x42 TIE fighter assembled from four synchronized sprite bobs.
;
; Each 24x21 quadrant overlays a dark-detail and light-hull hires sprite. All
; eight hardware sprites derive their coordinates from one 9-bit parent X.

!ifndef shiptransition_screen_base { shiptransition_screen_base = $0400 }
!ifndef shiptransition_charset_base { shiptransition_charset_base = $3000 }
!ifndef shiptransition_sprite_base { shiptransition_sprite_base = $2000 }
!ifndef shiptransition_vic_bank_base { shiptransition_vic_bank_base = $0000 }
!ifndef shiptransition_detail_color { shiptransition_detail_color = $0b }
!ifndef shiptransition_hull_color { shiptransition_hull_color = $0f }

SHIPTRANSITION_FIRST_POINTER = (shiptransition_sprite_base - shiptransition_vic_bank_base) / 64

shiptransition_build_assets:
    ldx #$00
shiptransition_copy_sprite_data:
    lda shiptransition_sprite_data+$000,x
    sta shiptransition_sprite_base+$000,x
    lda shiptransition_sprite_data+$100,x
    sta shiptransition_sprite_base+$100,x
    inx
    bne shiptransition_copy_sprite_data

    ldx #$1f
shiptransition_copy_star_charset:
    lda shiptransition_star_charset,x
    sta shiptransition_charset_base,x
    dex
    bpl shiptransition_copy_star_charset
    rts

shiptransition_init:
    lda #$1b
    sta $d011
    lda #$08
    sta $d016
    lda #$02                    ; screen $c000, charset $c800 in VIC bank 3
    sta $d018
    lda #$00
    sta $d020
    sta $d021
    sta $d017
    sta $d01b
    sta $d01c
    sta $d01d

    ldx #$00
shiptransition_clear_screen:
    sta shiptransition_screen_base+$000,x
    sta shiptransition_screen_base+$100,x
    sta shiptransition_screen_base+$200,x
    sta shiptransition_screen_base+$300,x
    sta $d800+$000,x
    sta $d800+$100,x
    sta $d800+$200,x
    sta $d800+$300,x
    inx
    bne shiptransition_clear_screen
    jsr shiptransition_draw_stars

    ldx #$00
shiptransition_init_sprites:
    txa
    clc
    adc #SHIPTRANSITION_FIRST_POINTER
    sta shiptransition_screen_base+$3f8,x
    txa
    and #$01
    tay
    lda shiptransition_layer_colors,y
    sta $d027,x
    inx
    cpx #$08
    bne shiptransition_init_sprites

    lda #$d0                    ; parent starts at x=464, just off the left edge
    sta shiptransition_parent_x_lo
    lda #$01
    sta shiptransition_parent_x_hi
    jsr shiptransition_position_sprites
    lda #$ff
    sta $d015
    rts

shiptransition_update:
    lda shiptransition_parent_x_lo
    clc
    adc #$04
    sta shiptransition_parent_x_lo
    bcc shiptransition_parent_ready
    inc shiptransition_parent_x_hi
    lda shiptransition_parent_x_hi
    and #$01
    sta shiptransition_parent_x_hi
shiptransition_parent_ready:
    jmp shiptransition_position_sprites

shiptransition_position_sprites:
    lda #$00
    sta shiptransition_x_msb
    ldx #$00
shiptransition_position_loop:
    lda shiptransition_parent_x_lo
    clc
    adc shiptransition_quadrant_x,x
    sta shiptransition_sprite_x
    lda shiptransition_parent_x_hi
    adc #$00
    and #$01
    sta shiptransition_sprite_x_hi

    txa
    asl
    tay
    lda shiptransition_sprite_x
    sta $d000,y
    lda shiptransition_sprite_y,x
    sta $d001,y

    lda shiptransition_sprite_x_hi
    beq shiptransition_next_sprite
    lda shiptransition_x_msb
    ora shiptransition_sprite_bits,x
    sta shiptransition_x_msb
shiptransition_next_sprite:
    inx
    cpx #$08
    bne shiptransition_position_loop
    lda shiptransition_x_msb
    sta $d010
    rts

shiptransition_hide:
    lda #$00
    sta $d015
    rts

shiptransition_draw_stars:
    ldx #$00
shiptransition_draw_star_loop:
    ldy shiptransition_star_rows,x
    lda shiptransition_screen_row_lo,y
    sta shiptransition_star_screen_store+1
    lda shiptransition_screen_row_hi,y
    sta shiptransition_star_screen_store+2
    lda shiptransition_color_row_lo,y
    sta shiptransition_star_color_store+1
    lda shiptransition_color_row_hi,y
    sta shiptransition_star_color_store+2
    ldy shiptransition_star_columns,x
    lda shiptransition_star_chars,x
shiptransition_star_screen_store:
    sta $ffff,y
    lda shiptransition_star_colors,x
shiptransition_star_color_store:
    sta $ffff,y
    inx
    cpx #SHIPTRANSITION_STAR_COUNT
    bne shiptransition_draw_star_loop
    rts

; Two sprite layers occupy each quadrant, so coordinates are repeated in pairs.
shiptransition_quadrant_x:
!byte 0,0,24,24,0,0,24,24
shiptransition_sprite_y:
!byte 98,98,98,98,119,119,119,119
shiptransition_layer_colors:
!byte shiptransition_detail_color,shiptransition_hull_color
shiptransition_sprite_bits:
!byte $01,$02,$04,$08,$10,$20,$40,$80

shiptransition_parent_x_lo:
!byte $00
shiptransition_parent_x_hi:
!byte $00
shiptransition_sprite_x:
!byte $00
shiptransition_sprite_x_hi:
!byte $00
shiptransition_x_msb:
!byte $00

SHIPTRANSITION_STAR_COUNT = 40
shiptransition_screen_row_lo:
!for row, 0, 24 { !byte <(shiptransition_screen_base + row * 40) }
shiptransition_screen_row_hi:
!for row, 0, 24 { !byte >(shiptransition_screen_base + row * 40) }
shiptransition_color_row_lo:
!for row, 0, 24 { !byte <($d800 + row * 40) }
shiptransition_color_row_hi:
!for row, 0, 24 { !byte >($d800 + row * 40) }

shiptransition_star_rows:
!byte 0,0,1,2,2,3,4,4,5,6,6,7,8,8,9,10,10,11,12,12
!byte 13,14,14,15,16,16,17,17,18,18,19,19,20,21,21,22,22,23,24,24
shiptransition_star_columns:
!byte 4,19,31,8,38,24,3,17,29,11,35,22,5,32,15,1,27,39,9,21
!byte 34,4,18,30,12,37,6,25,16,33,2,22,39,10,28,5,19,31,13,36
shiptransition_star_chars:
!byte 1,1,2,1,3,1,2,1,1,3,1,2,1,1,3,1,2,1,1,2
!byte 1,3,1,2,1,1,2,1,3,1,1,2,1,3,1,2,1,1,2,1
shiptransition_star_colors:
!byte 15,14,1,15,14,15,1,14,15,14,15,1,15,14,15,14,1,15,14,1
!byte 15,14,15,1,14,15,1,14,15,15,14,1,15,14,15,1,14,15,1,14

; Character zero is blank. The remaining three chars provide tiny, bright,
; and offset stars so the field does not read as a repeated tile pattern.
shiptransition_star_charset:
!byte $00,$00,$00,$00,$00,$00,$00,$00
!byte $00,$00,$00,$10,$00,$00,$00,$00
!byte $00,$00,$10,$38,$10,$00,$00,$00
!byte $00,$00,$00,$02,$00,$00,$00,$00

!source "src/generated/transition_sprites.inc"
