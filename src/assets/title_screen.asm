; Losslessly packed native multicolor Koala of the supplied Sixies branding.
; Stored packed rather than as raw bitmap/screen/color planes: the title is only
; ever drawn once per attract cycle, so it pays 10000 bytes of address space for
; a picture that compresses to under half that. ShowTitleScreen expands it
; through the same UnpackKoalaStream the Game Over reveal uses.
* = $1c80
TitleKoalaPacked:
!bin "src/assets/title_koala_packed.bin"
!source "src/assets/title_koala_tables.asm"
