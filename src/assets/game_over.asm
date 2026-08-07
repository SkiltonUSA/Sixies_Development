; Generated from src/assets/font/SixiesFont_image.asm.
; Nine source glyphs expanded into the large multicolor end banner.
* = $5f80
GameOverLabel:
; G
!byte $3c,$7e,$fc,$e0,$ee,$fe,$7e,$3c
; A
!byte $18,$3c,$7e,$7e,$e6,$ff,$ff,$e7
; M
!byte $66,$67,$ff,$ff,$ff,$db,$d3,$00
; E
!byte $7e,$7e,$7c,$7e,$7e,$7c,$7e,$7e
; space
!byte $00,$00,$00,$00,$00,$00,$00,$00
; O
!byte $3c,$7e,$ff,$e7,$e7,$ff,$7e,$3c
; V
!byte $e7,$e7,$f7,$7e,$7e,$3e,$3c,$18
; E
!byte $7e,$7e,$7c,$7e,$7e,$7c,$7e,$7e
; R
!byte $f8,$fc,$ee,$ee,$fc,$fc,$fe,$ee

; Expands one four-bit font nibble into four multicolor pixels.
GameOverMulticolorExpand:
!byte $00,$03,$0c,$0f,$30,$33,$3c,$3f
!byte $c0,$c3,$cc,$cf,$f0,$f3,$fc,$ff
