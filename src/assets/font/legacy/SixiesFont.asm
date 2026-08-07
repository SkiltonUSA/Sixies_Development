// Sixies C64 Font
// 8x8 monochrome glyphs, A-Z and 1-9
// Bit 7 = leftmost pixel, Bit 0 = rightmost pixel

SixiesFont:
// A
.byte $38,$6C,$C6,$C6,$FE,$C6,$C6,$00
// B
.byte $FC,$C6,$C6,$FC,$C6,$C6,$FC,$00
// C
.byte $7C,$C6,$C0,$C0,$C0,$C6,$7C,$00
// D
.byte $F8,$CC,$C6,$C6,$C6,$CC,$F8,$00
// E
.byte $FE,$C0,$C0,$FC,$C0,$C0,$FE,$00
// F
.byte $FE,$C0,$C0,$FC,$C0,$C0,$C0,$00
// G
.byte $7C,$C6,$C0,$DE,$C6,$C6,$7C,$00
// H
.byte $C6,$C6,$C6,$FE,$C6,$C6,$C6,$00
// I
.byte $7C,$18,$18,$18,$18,$18,$7C,$00
// J
.byte $1E,$06,$06,$06,$C6,$C6,$7C,$00
// K
.byte $C6,$CC,$D8,$F0,$D8,$CC,$C6,$00
// L
.byte $C0,$C0,$C0,$C0,$C0,$C0,$FE,$00
// M
.byte $C6,$EE,$FE,$D6,$C6,$C6,$C6,$00
// N
.byte $C6,$E6,$F6,$DE,$CE,$C6,$C6,$00
// O
.byte $7C,$C6,$C6,$C6,$C6,$C6,$7C,$00
// P
.byte $FC,$C6,$C6,$FC,$C0,$C0,$C0,$00
// Q
.byte $7C,$C6,$C6,$C6,$D6,$CC,$7A,$00
// R
.byte $FC,$C6,$C6,$FC,$D8,$CC,$C6,$00
// S
.byte $7C,$C6,$C0,$7C,$06,$C6,$7C,$00
// T
.byte $FE,$18,$18,$18,$18,$18,$18,$00
// U
.byte $C6,$C6,$C6,$C6,$C6,$C6,$7C,$00
// V
.byte $C6,$C6,$C6,$C6,$C6,$6C,$38,$00
// W
.byte $C6,$C6,$C6,$D6,$FE,$EE,$C6,$00
// X
.byte $C6,$C6,$6C,$38,$6C,$C6,$C6,$00
// Y
.byte $C6,$C6,$6C,$38,$18,$18,$18,$00
// Z
.byte $FE,$06,$0C,$18,$30,$60,$FE,$00
// 1
.byte $18,$38,$78,$18,$18,$18,$7E,$00
// 2
.byte $7C,$C6,$06,$1C,$70,$C0,$FE,$00
// 3
.byte $7C,$C6,$06,$3C,$06,$C6,$7C,$00
// 4
.byte $0C,$1C,$3C,$6C,$CC,$FE,$0C,$00
// 5
.byte $FE,$C0,$FC,$06,$06,$C6,$7C,$00
// 6
.byte $3C,$60,$C0,$FC,$C6,$C6,$7C,$00
// 7
.byte $FE,$06,$0C,$18,$30,$30,$30,$00
// 8
.byte $7C,$C6,$C6,$7C,$C6,$C6,$7C,$00
// 9
.byte $7C,$C6,$C6,$7E,$06,$0C,$78,$00

SixiesFontEnd:
.const SIXIES_GLYPH_COUNT = 35
.const SIXIES_GLYPH_BYTES = 8
