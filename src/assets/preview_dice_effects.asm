; Build active inverse and invalid dither variants in the VIC sprite workspace.
; Slots $30/$31 are inverse previews; $32/$33 are invalid previews.
* = $7f40

BuildPreviewDiceSprites:
    php
    sei
    lda #0
    sta previewBuildSlot
BuildPreviewDiceSprites_Next:
    ldx previewBuildSlot
    lda pieceValue0,x
    tay
    dey
    lda PreviewDiceSourceLo,y
    sta SOURCE_LO
    lda PreviewDiceSourceHi,y
    sta SOURCE_HI

    lda PreviewInverseTargetLo,x
    sta PTR_LO
    lda #>SHADOW_SPRITES
    sta PTR_HI
    lda PreviewShadowTargetLo,x
    sta BuildPreviewDiceSprites_StoreShadow + 1

    ldy #0
BuildPreviewDiceSprites_Byte:
    lda (SOURCE_LO),y
    sta shadowSourceByte
    tya
    and #1
    beq BuildPreviewDiceSprites_Even
    lda shadowSourceByte
    and #$55
    jmp BuildPreviewDiceSprites_StoreShadow
BuildPreviewDiceSprites_Even:
    lda shadowSourceByte
    and #$aa
BuildPreviewDiceSprites_StoreShadow:
    sta SHADOW_SPRITES + 128,y

    lda shadowSourceByte
    eor PreviewDiceSolidMask,y
    ora PreviewDiceOutlineMask,y
    sta (PTR_LO),y
    iny
    cpy #64
    bne BuildPreviewDiceSprites_Byte

    inc previewBuildSlot
    lda previewBuildSlot
    cmp #2
    bne BuildPreviewDiceSprites_Next
    plp
    rts

PreviewDiceSourceLo:
!byte <DieOneSprite,<DieTwoSprite,<DieThreeSprite
!byte <DieFourSprite,<DieFiveSprite,<DieSixSprite
PreviewDiceSourceHi:
!byte >DieOneSprite,>DieTwoSprite,>DieThreeSprite
!byte >DieFourSprite,>DieFiveSprite,>DieSixSprite
PreviewInverseTargetLo: !byte $00,$40
PreviewShadowTargetLo:  !byte $80,$c0
previewBuildSlot:       !byte 0

; The shared silhouette and its one-pixel inner outline. Inverse sprites are
; the source die's transparent pips combined with this outline.
* = $8e5d

PreviewDiceSolidMask:
!byte $0f,$ff,$f0,$1f,$ff,$f8,$3f,$ff
!byte $fc,$3f,$ff,$fc,$3f,$ff,$fc,$3f
!byte $ff,$fc,$3f,$ff,$fc,$3f,$ff,$fc
!byte $3f,$ff,$fc,$3f,$ff,$fc,$3f,$ff
!byte $fc,$3f,$ff,$fc,$3f,$ff,$fc,$3f
!byte $ff,$fc,$3f,$ff,$fc,$3f,$ff,$fc
!byte $3f,$ff,$fc,$3f,$ff,$fc,$1f,$ff
!byte $f8,$0f,$ff,$f0,$00,$00,$00,$00

PreviewDiceOutlineMask:
!byte $0f,$ff,$f0,$10,$00,$08,$20,$00
!byte $04,$20,$00,$04,$20,$00,$04,$20
!byte $00,$04,$20,$00,$04,$20,$00,$04
!byte $20,$00,$04,$20,$00,$04,$20,$00
!byte $04,$20,$00,$04,$20,$00,$04,$20
!byte $00,$04,$20,$00,$04,$20,$00,$04
!byte $20,$00,$04,$20,$00,$04,$10,$00
!byte $08,$0f,$ff,$f0,$00,$00,$00,$00
