; Three Y-expanded hi-res sprites form a 3x1 composite from the supplied 77x39
; chain-reaction art. The 72x40 rendition overlays the gameplay mascot and
; occupies only UI sprite slots, so all five board sprites stay visible during
; the chain pause.
* = $5a00

ChainReactionSpriteData:
!bin "src/assets/chain_reaction_sprite.bin"

; The packed callouts and their offset tables end below $3c80; bottom-control
; code starts at $3ed0.
* = $3c80

ShowChainReactionSprite:
    php
    sei
    lda #1
    sta chainReactionActive
    lda #%11100000
    sta uiEnableMask
    jsr ConfigureChainReactionSprites
    plp
    rts

ConfigureChainReactionSprites:
    ldx #2
ConfigureChainReactionSprites_Setup:
    txa
    clc
    adc #$68
    sta SPRITE0_PTR + 5,x
    lda ChainReactionSpriteColors,x
    sta SPRITE0_COLOR + 5,x
    txa
    asl
    tay
    lda ChainReactionSpriteXOffset,x
    clc
    adc #28
    sta SPRITE0_X + 10,y
    lda #112
    sta SPRITE0_Y + 10,y
    dex
    bpl ConfigureChainReactionSprites_Setup

    lda SPRITE_X_MSB
    and #%00011111
    sta SPRITE_X_MSB
    lda SPRITE_MULTICOLOR
    and #%00011111
    sta SPRITE_MULTICOLOR
    lda SPRITE_PRIORITY
    and #%00011111
    sta SPRITE_PRIORITY
    lda SPRITE_X_EXPAND
    and #%00011111
    sta SPRITE_X_EXPAND
    lda SPRITE_Y_EXPAND
    ora #%11100000
    sta SPRITE_Y_EXPAND
    lda #%11100000
    ora SPRITE_ENABLE
    sta SPRITE_ENABLE
    rts

HideChainReactionSprite:
    php
    sei
    lda #0
    sta chainReactionActive
    sta uiEnableMask
    lda SPRITE_ENABLE
    and #%00011111
    sta SPRITE_ENABLE
    lda SPRITE_X_EXPAND
    and #%00011111
    sta SPRITE_X_EXPAND
    lda SPRITE_Y_EXPAND
    and #%00011111
    sta SPRITE_Y_EXPAND
    plp
    jmp SetupPiecePreview

; The three tiles consume $5a00-$5abf. These small tables fit in the final gap
; immediately before the merge-firework sprite.
* = $5b80

ChainReactionSpriteXOffset:  !byte 0,24,48
ChainReactionSpriteColors:
    !byte COLOR_WHITE,COLOR_WHITE,COLOR_WHITE
