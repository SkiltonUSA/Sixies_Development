; Generated from src/assets/font/SixiesFont_image.asm.
; Nine source glyphs expanded into the large multicolor end banner.
* = $5f80
GameOverLabel:
; G
!byte $3c,$7e,$e0,$ee,$e6,$7e,$3c,$00
; A
!byte $38,$7c,$6c,$c6,$fe,$c6,$c6,$00
; M
!byte $c6,$ee,$fe,$d6,$c6,$c6,$c6,$00
; E
!byte $7c,$7c,$60,$78,$60,$7c,$7c,$00
; space
!byte $00,$00,$00,$00,$00,$00,$00,$00
; O
!byte $3c,$7e,$66,$66,$66,$7e,$3c,$00
; V
!byte $66,$66,$66,$7e,$7e,$3c,$18,$00
; E
!byte $7c,$7c,$60,$78,$60,$7c,$7c,$00
; R
!byte $7c,$7e,$66,$7c,$7c,$6c,$66,$00

; Expands one four-bit font nibble into four multicolor pixels.
GameOverMulticolorExpand:
!byte $00,$03,$0c,$0f,$30,$33,$3c,$3f
!byte $c0,$c3,$cc,$cf,$f0,$f3,$fc,$ff
