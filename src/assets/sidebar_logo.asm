; 80x32 hi-res Sixies logo for the top-right gameplay panel.
* = $4b84
DrawSidebarLogo:
    ldx #0
DrawSidebarLogo_BitmapRow:
    lda SidebarLogoBitmapSourceLo,x
    sta SOURCE_LO
    lda SidebarLogoBitmapSourceHi,x
    sta SOURCE_HI
    txa
    jsr SetBitmapRowPointer
    txa
    pha
    lda #LOGO_COLUMN
    jsr AddColumnOffset
    pla
    tax
    jsr UnpackKoalaStream
    inx
    cpx #4
    bne DrawSidebarLogo_BitmapRow

    ldx #0
DrawSidebarLogo_ScreenRow:
    lda SidebarLogoScreenSourceLo,x
    sta SOURCE_LO
    lda SidebarLogoScreenSourceHi,x
    sta SOURCE_HI
    txa
    jsr SetScreenRowPointer
    lda PTR_LO
    clc
    adc #LOGO_COLUMN
    sta PTR_LO
    bcc DrawSidebarLogo_ScreenTargetReady
    inc PTR_HI
DrawSidebarLogo_ScreenTargetReady:
    jsr UnpackKoalaStream
    inx
    cpx #4
    bne DrawSidebarLogo_ScreenRow
    rts

SidebarLogoBitmapSourceLo:
!byte <SidebarLogoBitmapRow0,<SidebarLogoBitmapRow1
!byte <SidebarLogoBitmapRow2,<SidebarLogoBitmapRow3
SidebarLogoBitmapSourceHi:
!byte >SidebarLogoBitmapRow0,>SidebarLogoBitmapRow1
!byte >SidebarLogoBitmapRow2,>SidebarLogoBitmapRow3
SidebarLogoScreenSourceLo:
!byte <SidebarLogoScreenRow0,<SidebarLogoScreenRow1
!byte <SidebarLogoScreenRow2,<SidebarLogoScreenRow3
SidebarLogoScreenSourceHi:
!byte >SidebarLogoScreenRow0,>SidebarLogoScreenRow1
!byte >SidebarLogoScreenRow2,>SidebarLogoScreenRow3

!source "src/assets/sidebar_logo_packed.asm"
