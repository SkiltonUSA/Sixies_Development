; Opposing 48x42 TIE fighter and X-wing composites, raster multiplexed.
;
; Each 24x21 quadrant overlays detail and hull hires sprites. All eight hardware
; sprites are reused below the TIE scanlines to draw the lower X-wing.

!ifndef shiptransition_screen_base { shiptransition_screen_base = $0400 }
!ifndef shiptransition_sprite_base { shiptransition_sprite_base = $2000 }
!ifndef shiptransition_vic_bank_base { shiptransition_vic_bank_base = $0000 }
!ifndef shiptransition_detail_color { shiptransition_detail_color = $0b }
!ifndef shiptransition_hull_color { shiptransition_hull_color = $0f }
!ifndef shiptransition_xwing_detail_color { shiptransition_xwing_detail_color = $08 }
!ifndef shiptransition_xwing_hull_color { shiptransition_xwing_hull_color = $0f }

SHIPTRANSITION_TIE_FIRST_POINTER = (shiptransition_sprite_base - shiptransition_vic_bank_base) / 64
SHIPTRANSITION_XWING_FIRST_POINTER = SHIPTRANSITION_TIE_FIRST_POINTER + 8
SHIPTRANSITION_XWING_RASTER = 156

shiptransition_build_assets:
    ldx #$00
shiptransition_copy_sprite_data:
    lda shiptransition_sprite_data+$000,x
    sta shiptransition_sprite_base+$000,x
    lda shiptransition_sprite_data+$100,x
    sta shiptransition_sprite_base+$100,x
    lda shiptransition_sprite_data+$200,x
    sta shiptransition_sprite_base+$200,x
    lda shiptransition_sprite_data+$300,x
    sta shiptransition_sprite_base+$300,x
    inx
    bne shiptransition_copy_sprite_data
    rts

shiptransition_init:
    lda #$3b                    ; show the demo's prepared hires bitmap stars
    sta $d011
    lda #$08
    sta $d016
    lda #$08                    ; screen $c000, bitmap $e000 in VIC bank 3
    sta $d018
    lda #$00
    sta $d020
    sta $d021
    sta $d017
    sta $d01b
    sta $d01c
    sta $d01d

    lda #$d0                    ; parent starts at x=464, just off the left edge
    sta shiptransition_tie_x_lo
    lda #$01
    sta shiptransition_tie_x_hi
    lda #$58                    ; X-wing starts at x=344, just off the right edge
    sta shiptransition_xwing_x_lo
    lda #$01
    sta shiptransition_xwing_x_hi
    jsr shiptransition_select_tie
    lda #$ff
    sta $d015
    rts

shiptransition_update:
    lda shiptransition_tie_x_lo
    clc
    adc #$04
    sta shiptransition_tie_x_lo
    bcc shiptransition_tie_ready
    inc shiptransition_tie_x_hi
    lda shiptransition_tie_x_hi
    and #$01
    sta shiptransition_tie_x_hi
shiptransition_tie_ready:
    lda shiptransition_xwing_x_lo
    sec
    sbc #$04
    sta shiptransition_xwing_x_lo
    lda shiptransition_xwing_x_hi
    sbc #$00
    and #$01
    sta shiptransition_xwing_x_hi
    jmp shiptransition_select_tie

shiptransition_show_xwing:
    lda $d012
    cmp #SHIPTRANSITION_XWING_RASTER
    bne shiptransition_show_xwing
    jmp shiptransition_select_xwing

shiptransition_select_tie:
    ldx #$00
shiptransition_select_tie_loop:
    txa
    clc
    adc #SHIPTRANSITION_TIE_FIRST_POINTER
    sta shiptransition_screen_base+$3f8,x
    txa
    and #$01
    tay
    lda shiptransition_tie_layer_colors,y
    sta $d027,x
    inx
    cpx #$08
    bne shiptransition_select_tie_loop
    lda shiptransition_tie_x_lo
    sta shiptransition_active_x_lo
    lda shiptransition_tie_x_hi
    sta shiptransition_active_x_hi
    lda #98
    sta shiptransition_active_y
    jmp shiptransition_position_sprites

shiptransition_select_xwing:
    ldx #$00
shiptransition_select_xwing_loop:
    txa
    clc
    adc #SHIPTRANSITION_XWING_FIRST_POINTER
    sta shiptransition_screen_base+$3f8,x
    txa
    and #$01
    tay
    lda shiptransition_xwing_layer_colors,y
    sta $d027,x
    inx
    cpx #$08
    bne shiptransition_select_xwing_loop
    lda shiptransition_xwing_x_lo
    sta shiptransition_active_x_lo
    lda shiptransition_xwing_x_hi
    sta shiptransition_active_x_hi
    lda #186
    sta shiptransition_active_y
    jmp shiptransition_position_sprites

shiptransition_position_sprites:
    lda #$00
    sta shiptransition_x_msb
    ldx #$00
shiptransition_position_loop:
    lda shiptransition_active_x_lo
    clc
    adc shiptransition_quadrant_x,x
    sta shiptransition_sprite_x
    lda shiptransition_active_x_hi
    adc #$00
    and #$01
    sta shiptransition_sprite_x_hi

    txa
    asl
    tay
    lda shiptransition_sprite_x
    sta $d000,y
    lda shiptransition_active_y
    clc
    adc shiptransition_quadrant_y,x
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

; Two sprite layers occupy each quadrant, so coordinates are repeated in pairs.
shiptransition_quadrant_x:
!byte 0,0,24,24,0,0,24,24
shiptransition_quadrant_y:
!byte 0,0,0,0,21,21,21,21
shiptransition_tie_layer_colors:
!byte shiptransition_detail_color,shiptransition_hull_color
shiptransition_xwing_layer_colors:
!byte shiptransition_xwing_detail_color,shiptransition_xwing_hull_color
shiptransition_sprite_bits:
!byte $01,$02,$04,$08,$10,$20,$40,$80

shiptransition_tie_x_lo:
!byte $00
shiptransition_tie_x_hi:
!byte $00
shiptransition_xwing_x_lo:
!byte $00
shiptransition_xwing_x_hi:
!byte $00
shiptransition_active_x_lo:
!byte $00
shiptransition_active_x_hi:
!byte $00
shiptransition_active_y:
!byte $00
shiptransition_sprite_x:
!byte $00
shiptransition_sprite_x_hi:
!byte $00
shiptransition_x_msb:
!byte $00

!source "src/generated/transition_sprites.inc"
!source "src/generated/plasma_tie_sprite.inc"
