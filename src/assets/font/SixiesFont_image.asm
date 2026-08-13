// Sixies font reproduced from SixiesFont_sheet.png
// 8x8 monochrome glyphs, A-Z and 0-9
// Bit 7 = leftmost pixel, Bit 0 = rightmost pixel

SixiesFont:
// A
.byte $38,$7C,$6C,$C6,$FE,$C6,$C6,$00
// B
.byte $7C,$7E,$6E,$7C,$6E,$7E,$7C,$00
// C
.byte $3C,$7E,$E6,$E0,$E6,$7E,$3C,$00
// D
.byte $78,$7C,$7E,$66,$7E,$7C,$78,$00
// E
.byte $7C,$7C,$60,$78,$60,$7C,$7C,$00
// F
.byte $7C,$7E,$70,$7C,$7C,$70,$60,$00
// G
.byte $3C,$7E,$E0,$EE,$E6,$7E,$3C,$00
// H
.byte $66,$66,$7E,$7E,$7E,$66,$66,$00
// I
.byte $38,$38,$38,$38,$38,$38,$38,$00
// J
.byte $0C,$0C,$0C,$0E,$7C,$7C,$38,$00
// K
.byte $66,$6C,$78,$70,$78,$6C,$66,$00
// L
.byte $60,$70,$70,$70,$70,$7C,$7C,$00
// M
.byte $C6,$EE,$FE,$D6,$C6,$C6,$C6,$00
// N
.byte $66,$76,$7E,$7E,$7E,$6E,$66,$00
// O
.byte $3C,$7E,$66,$66,$66,$7E,$3C,$00
// P
.byte $78,$7C,$6E,$7E,$7C,$70,$60,$00
// Q
.byte $78,$7C,$EE,$CE,$FE,$7C,$3E,$0E
// R
.byte $7C,$7E,$66,$7C,$7C,$6C,$66,$00
// S
.byte $3C,$7E,$70,$3C,$1E,$7E,$3C,$00
// T
.byte $7E,$7E,$38,$18,$18,$18,$18,$00
// U
.byte $66,$66,$66,$66,$7E,$7E,$3C,$00
// V
.byte $66,$66,$66,$7E,$7E,$3C,$18,$00
// W
.byte $C6,$C6,$D6,$D6,$FE,$FE,$6C,$00
// X
.byte $C6,$C6,$6C,$38,$6C,$C6,$C6,$00
// Y
.byte $66,$7E,$7E,$3C,$18,$18,$18,$00
// Z
.byte $7C,$7E,$1C,$38,$70,$7E,$7C,$00
// 0
.byte $3C,$7E,$66,$66,$66,$7E,$3C,$00
// 1
.byte $1C,$3C,$3C,$1C,$1C,$1C,$1C,$00
// 2
.byte $7C,$7E,$0C,$38,$70,$7E,$7E,$00
// 3
.byte $3C,$7E,$0E,$1C,$0E,$7E,$3C,$00
// 4
.byte $18,$38,$6C,$CC,$FE,$0C,$0C,$00
// 5
.byte $7C,$7C,$70,$7C,$0E,$7E,$78,$00
// 6
.byte $3C,$38,$78,$7E,$6E,$7E,$3C,$00
// 7
.byte $7E,$7E,$1C,$18,$38,$38,$30,$00
// 8
.byte $3C,$7E,$6C,$3C,$6E,$7E,$3C,$00
// 9
.byte $3C,$66,$66,$3E,$0C,$1C,$38,$00

SixiesFontEnd:
.const SIXIES_GLYPH_COUNT = 36
.const SIXIES_GLYPH_BYTES = 8
