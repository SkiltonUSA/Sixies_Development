; Three native-resolution hi-res sprites form a 3x1 composite from the supplied
; chain-reaction art. It occupies the right-side UI sprite slots so all five
; board sprites remain untouched during the pause before a later chain merge.
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
    lda ChainReactionSpriteX,x
    sta SPRITE0_X + 10,y
    lda #158
    sta SPRITE0_Y + 10,y
    dex
    bpl ConfigureChainReactionSprites_Setup

    lda SPRITE_X_MSB
    and #%00011111
    ora #%11100000
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
    and #%00011111
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

; Low bytes of X=268,292,316 keep the 72-pixel banner inside the right panel.
ChainReactionSpriteX:        !byte 12,36,60
ChainReactionSpriteColors:
    !byte COLOR_WHITE,COLOR_WHITE,COLOR_WHITE
