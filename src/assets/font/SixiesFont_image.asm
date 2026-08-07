// Sixies font extracted from SixiesFont_sheet.png
// 8x8 monochrome glyphs, A-Z and 0-9
// Bit 7 = leftmost pixel, Bit 0 = rightmost pixel

SixiesFont:
// A
.byte $18,$3C,$7E,$7E,$E6,$FF,$FF,$E7
// B
.byte $F8,$FC,$EE,$FC,$FE,$EE,$FE,$FC
// C
.byte $3C,$7E,$FE,$E0,$E0,$FE,$7E,$3C
// D
.byte $F8,$FC,$FE,$EE,$EE,$FE,$FC,$F8
// E
.byte $7E,$7E,$7C,$7E,$7E,$7C,$7E,$7E
// F
.byte $7E,$7E,$7C,$7C,$7E,$70,$70,$70
// G
.byte $3C,$7E,$FC,$E0,$EE,$FE,$7E,$3C
// H
.byte $EE,$EE,$EE,$FE,$FE,$EE,$EE,$EE
// I
.byte $18,$38,$38,$38,$38,$38,$38,$38
// J
.byte $06,$0E,$0E,$0E,$0E,$6E,$7E,$3C
// K
.byte $CC,$EE,$FC,$FC,$FC,$FC,$EE,$CE
// L
.byte $60,$70,$70,$70,$70,$7C,$7E,$7E
// M
.byte $66,$67,$FF,$FF,$FF,$DB,$D3,$00
// N
.byte $C6,$EE,$FE,$FE,$FE,$FE,$EE,$C6
// O
.byte $3C,$7E,$FF,$E7,$E7,$FF,$7E,$3C
// P
.byte $F8,$FE,$EE,$EE,$FE,$FC,$E0,$E0
// Q
.byte $3C,$7E,$EE,$E7,$EF,$FE,$7F,$03
// R
.byte $F8,$FC,$EE,$EE,$FC,$FC,$FE,$EE
// S
.byte $3C,$3E,$76,$3C,$3E,$6E,$7E,$3C
// T
.byte $FE,$FE,$7C,$38,$38,$38,$38,$38
// U
.byte $E7,$E7,$E7,$E7,$E7,$FF,$7E,$3C
// V
.byte $E7,$E7,$F7,$7E,$7E,$3E,$3C,$18
// W
.byte $00,$DB,$DB,$FF,$7E,$7E,$6E,$00
// X
.byte $E7,$EF,$FE,$7E,$7E,$FE,$FF,$E7
// Y
.byte $E7,$F7,$FF,$7E,$3C,$3C,$3C,$18
// Z
.byte $FC,$FE,$7C,$3C,$78,$FC,$FE,$FE
// 0
.byte $38,$FC,$FE,$EE,$EE,$FE,$FE,$78
// 1
.byte $1C,$3C,$3C,$1C,$1C,$1C,$1C,$1C
// 2
.byte $78,$FC,$FE,$1C,$3C,$78,$FE,$FE
// 3
.byte $3C,$7E,$6E,$3C,$1E,$6E,$7E,$3C
// 4
.byte $1C,$3C,$7C,$6C,$EC,$FE,$FE,$0C
// 5
.byte $3E,$7E,$70,$7C,$3E,$6E,$7E,$3C
// 6
.byte $18,$38,$70,$7C,$7E,$7E,$7E,$3C
// 7
.byte $7E,$7E,$3E,$1C,$1C,$18,$38,$38
// 8
.byte $78,$FC,$EE,$7C,$FE,$EE,$FE,$7C
// 9
.byte $3C,$7E,$7E,$7E,$3E,$0E,$3C,$18

SixiesFontEnd:
.const SIXIES_GLYPH_COUNT = 36
.const SIXIES_GLYPH_BYTES = 8
