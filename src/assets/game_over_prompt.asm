; Generated from src/assets/font/SixiesFont_image.asm.
; Compact multicolor PRESS N FOR NEW GAME end-screen prompt.
* = $4ad0
GameOverPrompt:
!byte $ff,$c0,$c0,$ff,$c0,$c0,$c0,$00,$0f,$cc,$cc,$0f,$0c,$0c,$0c,$00
!byte $f0,$0c,$0c,$f0,$c0,$30,$0c,$00,$ff,$c0,$c0,$ff,$c0,$c0,$ff,$00
!byte $c3,$0c,$0c,$03,$00,$00,$cf,$00,$fc,$00,$00,$f0,$0c,$0c,$f0,$00
!byte $3f,$c0,$c0,$3f,$00,$00,$ff,$00,$c0,$00,$00,$00,$c0,$c0,$00,$00
!byte $00,$00,$00,$00,$00,$00,$00,$00,$c0,$f0,$cc,$cc,$c3,$c3,$c0,$00
!byte $c0,$c0,$c0,$c0,$c0,$c0,$c0,$00,$00,$00,$00,$00,$00,$00,$00,$00
!byte $ff,$c0,$c0,$ff,$c0,$c0,$c0,$00,$c3,$0c,$0c,$0c,$0c,$0c,$03,$00
!byte $f0,$0c,$0c,$0c,$0c,$0c,$f0,$00,$ff,$c0,$c0,$ff,$cc,$c3,$c0,$00
!byte $00,$c0,$c0,$00,$00,$00,$c0,$00,$00,$00,$00,$00,$00,$00,$00,$00
!byte $c0,$f0,$cc,$cc,$c3,$c3,$c0,$00,$cf,$cc,$cc,$cf,$cc,$cc,$cf,$00
!byte $fc,$00,$00,$f0,$00,$00,$fc,$00,$c0,$c0,$c0,$cc,$cc,$cc,$33,$00
!byte $c0,$c0,$c0,$c0,$c0,$c0,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
!byte $3f,$c0,$c0,$cf,$c0,$c0,$3f,$00,$03,$cc,$0c,$cf,$cc,$cc,$0c,$00
!byte $f0,$0c,$0c,$fc,$0c,$0c,$0c,$00,$c0,$f3,$cc,$cc,$c0,$c0,$c0,$00
!byte $cf,$cc,$cc,$cf,$cc,$cc,$cf,$00,$fc,$00,$00,$f0,$00,$00,$fc,$00

DrawGameOverPrompt:
    lda #<GameOverPrompt
    sta SOURCE_LO
    lda #>GameOverPrompt
    sta SOURCE_HI
    lda #<(BITMAP + (23 * 320) + (5 * 8))
    sta PTR_LO
    lda #>(BITMAP + (23 * 320) + (5 * 8))
    sta PTR_HI
    ldy #0
DrawGameOverPrompt_Copy:
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    cpy #240
    bne DrawGameOverPrompt_Copy
    ldx #29
    lda #COLOR_WHITE
DrawGameOverPrompt_Color:
    sta COLOR_RAM + (23 * 40) + 5,x
    dex
    bpl DrawGameOverPrompt_Color
    rts
