; Packed 72x64 Chain Reaction bitmap panel. It uses the same right-sidebar
; position, decoder, and screen colors as the normal merge exclamation words.
; The legacy filename remains so existing asset targets keep working.
* = $5a00

ChainReactionCalloutPackedData:
!bin "src/assets/chain_reaction_sprite.bin"

; The merge-callout tables end below this gap; bottom-control code starts at
; $3d20. No hardware sprites are borrowed by this effect.
* = $3c80

ShowChainReactionCallout:
    php
    sei
    jsr SetMergeCalloutPosition
    jsr ClearMascotPanel
    lda #<ChainReactionCalloutPackedData
    sta SOURCE_LO
    lda #>ChainReactionCalloutPackedData
    sta SOURCE_HI
    lda #COLOR_WHITE
    jsr SetMascotPanelColor
    jsr DecodeMascotMergeCallout
    plp
    rts

HideChainReactionCallout:
    php
    sei
    jsr ClearMascotPanel
    lda #COLOR_DKGRAY
    jsr SetMascotPanelColor
    plp
    rts
