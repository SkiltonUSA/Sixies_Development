; ---------------------------------------------------------------------------
; Persistent ten-entry high-score table and three-initial editor.
;
; The 56-byte checksummed table lives at the start of reserved disk sector 720.
; Direct SIO keeps the feature independent of DOS and works with the PicoBoot
; disk. A missing/read-only disk falls back to the same seeded table in RAM.
; ---------------------------------------------------------------------------

HIGH_SCORE_COUNT       = 10
HIGH_SCORE_ENTRY_BYTES = 5
HIGH_SCORE_DATA_OFFSET = 6
HIGH_SCORE_BYTES       = 56
HIGH_SCORE_SECTOR      = 720
HIGH_SCORE_ROW_TOP     = 44
HIGH_SCORE_NAME_COLUMN = 15

DDEVIC = $0300
DUNIT  = $0301
DCOMND = $0302
DSTATS = $0303
DBUFLO = $0304
DBUFHI = $0305
DTIMLO = $0306
DUNUSE = $0307
DBYTLO = $0308
DBYTHI = $0309
DAUX1  = $030A
DAUX2  = $030B
SIOV   = $E459

.segment "ZEROPAGE"
zp_high_score:        .res 2
zp_high_score_src:    .res 2

.segment "BSS"
high_score_sector:    .res 128
high_score_ranked:    .res 1
high_score_row_index: .res 1
high_score_digit_index: .res 1
high_score_edit_pos:  .res 1
high_score_editing:   .res 1
high_score_joy_latch: .res 1
high_score_work_lo:   .res 1
high_score_work_hi:   .res 1
high_score_digit:     .res 1
high_score_visible:   .res 1
high_score_line:      .res 16
high_score_chars:     .res 4

.segment "AUXCODE"

; Load the persistent sector once at startup. Invalid or absent data is reset
; to the reference screen's seeded scores and saved when the disk is writable.
high_scores_init:
    lda #0
    sta high_score_editing
    jsr high_scores_disk_read
    bcs @defaults
    jsr high_scores_valid
    bcc @done
@defaults:
    jsr high_scores_reset
    jsr high_scores_save
@done:
    rts

high_scores_reset:
    ldx #HIGH_SCORE_BYTES-1
@copy:
    lda high_score_defaults,x
    sta high_score_sector,x
    dex
    bpl @copy
    rts

; Carry clear means the magic/version/checksum are valid.
high_scores_valid:
    lda high_score_sector+0
    cmp #'S'
    bne @bad
    lda high_score_sector+1
    cmp #'I'
    bne @bad
    lda high_score_sector+2
    cmp #'X'
    bne @bad
    lda high_score_sector+3
    cmp #'H'
    bne @bad
    lda high_score_sector+4
    cmp #1
    bne @bad
    jsr high_scores_checksum
    cmp high_score_sector+5
    bne @bad
    clc
    rts
@bad:
    sec
    rts

high_scores_checksum:
    lda #0
    ldx #HIGH_SCORE_DATA_OFFSET
@sum:
    clc
    adc high_score_sector,x
    inx
    cpx #HIGH_SCORE_BYTES
    bne @sum
    rts

high_scores_save:
    jsr high_scores_checksum
    sta high_score_sector+5
    lda #$50                    ; POKEY/SIO PUT SECTOR without verify
    ldx #$80                    ; computer-to-disk transfer
    jmp high_scores_sio

high_scores_disk_read:
    lda #$52                    ; SIO READ SECTOR
    ldx #$40                    ; disk-to-computer transfer

; A=command, X=direction. Carry clear on SIO completion code 1.
high_scores_sio:
    sta DCOMND
    stx DSTATS
    lda #$31
    sta DDEVIC
    lda #1
    sta DUNIT
    lda #<high_score_sector
    sta DBUFLO
    lda #>high_score_sector
    sta DBUFHI
    lda #7
    sta DTIMLO
    lda #0
    sta DUNUSE
    lda #128
    sta DBYTLO
    lda #0
    sta DBYTHI
    lda #<HIGH_SCORE_SECTOR
    sta DAUX1
    lda #>HIGH_SCORE_SECTOR
    sta DAUX2
    jsr SIOV
    lda DSTATS
    cmp #1
    beq @ok
    sec
    rts
@ok:
    clc
    rts

; Point zp_high_score at entry X (three initials, little-endian score).
high_score_entry_ptr:
    lda high_score_entry_offsets,x
    clc
    adc #<high_score_sector
    sta zp_high_score
    lda #>high_score_sector
    adc #0
    sta zp_high_score+1
    rts

; Return the insertion rank in A. Equal scores do not displace an existing
; entry, matching the Apple II rules.
high_score_rank:
    ldx #0
@entry:
    jsr high_score_entry_ptr
    ldy #4
    lda score_hi
    cmp (zp_high_score),y
    bcc @next
    bne @found
    dey
    lda score_lo
    cmp (zp_high_score),y
    bcc @next
    beq @next
@found:
    txa
    rts
@next:
    inx
    cpx #HIGH_SCORE_COUNT
    bne @entry
    lda #HIGH_SCORE_COUNT
    rts

; Called after the Game Over page has been acknowledged. It inserts and edits
; a qualifying score, or simply presents the current table otherwise.
high_scores_after_game:
    jsr high_score_rank
    sta high_score_ranked
    cmp #HIGH_SCORE_COUNT
    bcs @show_only
    jsr high_score_insert
    jmp high_score_edit_initials
@show_only:
    lda #0
    sta high_score_editing
    lda #HIGH_SCORE_COUNT
    jmp show_high_scores

; Shift lower entries down and insert AAA plus the current score at the rank.
high_score_insert:
    ldx #HIGH_SCORE_COUNT-1
@shift:
    cpx high_score_ranked
    beq @new_entry
    jsr high_score_entry_ptr
    lda zp_high_score
    sta zp_high_score_src
    lda zp_high_score+1
    sta zp_high_score_src+1
    sec
    lda zp_high_score_src
    sbc #HIGH_SCORE_ENTRY_BYTES
    sta zp_high_score_src
    lda zp_high_score_src+1
    sbc #0
    sta zp_high_score_src+1
    ldy #HIGH_SCORE_ENTRY_BYTES-1
@copy:
    lda (zp_high_score_src),y
    sta (zp_high_score),y
    dey
    bpl @copy
    dex
    bpl @shift

@new_entry:
    ldx high_score_ranked
    jsr high_score_entry_ptr
    lda #'A'
    ldy #0
    sta (zp_high_score),y
    iny
    sta (zp_high_score),y
    iny
    sta (zp_high_score),y
    iny
    lda score_lo
    sta (zp_high_score),y
    iny
    lda score_hi
    sta (zp_high_score),y
    rts

high_score_edit_initials:
    lda #1
    sta high_score_editing
    lda high_score_ranked
    jsr show_high_scores
    lda #0
    sta high_score_edit_pos
    lda #1
    sta high_score_joy_latch
    lda #CH_NONE
    sta CH
    jsr high_score_draw_edit_row

@poll:
    lda #0
    sta ATRACT
    lda CH
    cmp #CH_NONE
    beq @joystick
    sta high_score_row_index
    lda #CH_NONE
    sta CH
    lda high_score_row_index
    and #KEY_CODE_MASK
    cmp #KEY_RETURN
    beq @accept
    cmp #KEY_SPACE
    beq @accept
    cmp #KEY_DELETE
    bne :+
    jmp @left
:
    tax
    lda high_score_key_letters,x
    beq @poll
    jsr high_score_store_letter
    jmp @advance

@joystick:
    lda STRIG0
    beq @fire
    lda STICK0
    and #$0F
    cmp #$0F
    bne @direction
    lda STRIG1
    beq @fire
    lda STICK1
    and #$0F
    cmp #$0F
    bne @direction
    lda #0
    sta high_score_joy_latch
    jmp @poll

@fire:
    lda high_score_joy_latch
    bne @poll
    lda #1
    sta high_score_joy_latch
@accept:
@advance:
    inc high_score_edit_pos
    lda high_score_edit_pos
    cmp #3
    bcc @redraw
    jsr high_scores_save
    lda #0
    sta high_score_editing
    lda high_score_ranked
    jmp show_high_scores

@direction:
    sta high_score_row_index
    lda high_score_joy_latch
    beq :+
    jmp @poll
:
    lda #1
    sta high_score_joy_latch
    lda high_score_row_index
    cmp #$0E
    beq @up
    cmp #$0D
    beq @down
    cmp #$0B
    beq @left
    cmp #$07
    beq @right
    jmp @poll

@up:
    jsr high_score_current_letter
    cmp #'Z'
    bne :+
    lda #'A'-1
:
    clc
    adc #1
    jsr high_score_store_letter
    jmp @redraw
@down:
    jsr high_score_current_letter
    cmp #'A'
    bne :+
    lda #'Z'+1
:
    sec
    sbc #1
    jsr high_score_store_letter
    jmp @redraw
@left:
    lda high_score_edit_pos
    beq @redraw
    dec high_score_edit_pos
    jmp @redraw
@right:
    lda high_score_edit_pos
    cmp #2
    beq @redraw
    inc high_score_edit_pos
@redraw:
    jsr high_score_draw_edit_row
    jmp @poll

high_score_current_letter:
    ldx high_score_ranked
    jsr high_score_entry_ptr
    ldy high_score_edit_pos
    lda (zp_high_score),y
    rts

; A=ASCII letter.
high_score_store_letter:
    pha
    ldx high_score_ranked
    jsr high_score_entry_ptr
    ldy high_score_edit_pos
    pla
    sta (zp_high_score),y
    rts

; Redraw the three initials and underline the selected position.
high_score_draw_edit_row:
    ldx high_score_ranked
    jsr high_score_entry_ptr
    ldy #0
@chars:
    lda (zp_high_score),y
    sta high_score_chars,y
    iny
    cpy #3
    bne @chars
    lda #0
    sta high_score_chars+3
    lda #<high_score_chars
    sta zp_text
    lda #>high_score_chars
    sta zp_text+1
    ldx high_score_ranked
    lda high_score_row_y,x
    ldx #HIGH_SCORE_NAME_COLUMN
    jsr draw_text

    ldx high_score_ranked
    lda high_score_row_y,x
    clc
    adc #8
    jsr set_screen_row
    lda #0
    ldy #HIGH_SCORE_NAME_COLUMN
    sta (zp_screen),y
    iny
    sta (zp_screen),y
    iny
    sta (zp_screen),y
    lda high_score_edit_pos
    clc
    adc #HIGH_SCORE_NAME_COLUMN
    tay
    lda #$FF
    sta (zp_screen),y
    rts

; A is the newly inserted rank or 10 when no row should be marked.
show_high_scores:
    sta high_score_ranked
    jsr video_update_begin
    jsr high_score_clear_screen

    lda #<high_score_title
    sta zp_text
    lda #>high_score_title
    sta zp_text+1
    lda #8
    ldx #11
    jsr draw_text

    lda #28
    jsr set_screen_row
    lda #$FF
    ldy #3
@line:
    sta (zp_screen),y
    iny
    cpy #37
    bne @line

    lda #<high_score_header
    sta zp_text
    lda #>high_score_header
    sta zp_text+1
    lda #34
    ldx #10
    jsr draw_text

    jsr draw_mascot
    lda #5
    ldx #31
    jsr draw_sidebar_die
    lda #6
    ldx #35
    jsr draw_sidebar_die

    ldx #0
@rows:
    stx high_score_row_index
    jsr high_score_build_line
    lda #<high_score_line
    sta zp_text
    lda #>high_score_line
    sta zp_text+1
    ldx high_score_row_index
    lda high_score_row_y,x
    ldx #10
    jsr draw_text
    ldx high_score_row_index
    inx
    cpx #HIGH_SCORE_COUNT
    bne @rows

    lda high_score_editing
    beq @restart_prompt
    lda #<high_score_edit_prompt
    sta zp_text
    lda #>high_score_edit_prompt
    sta zp_text+1
    bne @draw_prompt
@restart_prompt:
    lda #<high_score_restart_prompt
    sta zp_text
    lda #>high_score_restart_prompt
    sta zp_text+1
@draw_prompt:
    lda #176
    ldx #3
    jsr draw_text
    jmp video_update_end

high_score_clear_screen:
    lda #<SCREEN
    sta zp_screen
    lda #>SCREEN
    sta zp_screen+1
    lda #0
    ldx #SCREEN_PHYSICAL_PAGES
    ldy #0
@byte:
    sta (zp_screen),y
    iny
    bne @byte
    inc zp_screen+1
    dex
    bne @byte
    rts

high_score_build_line:
    lda #' '
    ldx #14
@clear:
    sta high_score_line,x
    dex
    bpl @clear
    lda #0
    sta high_score_line+15

    ldx high_score_row_index
    cpx high_score_ranked
    bne :+
    lda #'>'
    sta high_score_line+0
:
    cpx #9
    bne @single_rank
    lda #'1'
    sta high_score_line+1
    lda #'0'
    bne @rank_ready
@single_rank:
    lda #' '
    sta high_score_line+1
    txa
    clc
    adc #'1'
@rank_ready:
    sta high_score_line+2
    lda #'.'
    sta high_score_line+3

    ldx high_score_row_index
    jsr high_score_entry_ptr
    ldy #0
@initials:
    lda (zp_high_score),y
    sta high_score_line+5,y
    iny
    cpy #3
    bne @initials
    ldy #3
    lda (zp_high_score),y
    sta high_score_work_lo
    iny
    lda (zp_high_score),y
    sta high_score_work_hi

    lda #0
    sta high_score_visible
    ldx #0
@digit:
    stx high_score_digit_index
    lda #0
    sta high_score_digit
@subtract:
    ldx high_score_digit_index
    lda high_score_work_hi
    cmp score_div_hi,x
    bcc @store_digit
    bne @can_subtract
    lda high_score_work_lo
    cmp score_div_lo,x
    bcc @store_digit
@can_subtract:
    sec
    lda high_score_work_lo
    sbc score_div_lo,x
    sta high_score_work_lo
    lda high_score_work_hi
    sbc score_div_hi,x
    sta high_score_work_hi
    inc high_score_digit
    jmp @subtract
@store_digit:
    lda high_score_digit
    bne @visible
    cpx #4
    beq @visible
    lda high_score_visible
    bne @visible_digit
    lda #' '
    bne @write_digit
@visible:
    lda #1
    sta high_score_visible
@visible_digit:
    lda high_score_digit
    clc
    adc #'0'
@write_digit:
    ldx high_score_digit_index
    sta high_score_line+10,x
    inx
    cpx #5
    bne @digit
    rts

high_score_entry_offsets:
    .byte 6,11,16,21,26,31,36,41,46,51
high_score_row_y:
    .byte 44,56,68,80,92,104,116,128,140,152

high_score_title:          .asciiz "SIXIES HIGH SCORES"
high_score_header:         .asciiz " RNK NAME  SCORE"
high_score_restart_prompt: .asciiz "SPACE FIRE OR N STARTS A NEW GAME"
high_score_edit_prompt:    .asciiz "ENTER 3 INITIALS TYPE OR USE JOYSTICK"

; Direct KBCODE-to-ASCII map for letter entry; nonletters are zero.
high_score_key_letters:
    .byte 'L','J',0,0,0,'K',0,0
    .byte 'O',0,'P','U',0,'I',0,0
    .byte 'V',0,'C',0,0,'B','X','Z'
    .byte 0,0,0,0,0,0,0,0
    .byte 0,0,0,'N',0,'M',0,0
    .byte 'R',0,'E','Y',0,'T','W','Q'
    .byte 0,0,0,0,0,0,0,0
    .byte 'F','H','D',0,0,'G','S','A'

; Signature, version, checksum, then ten {initials, score-lo, score-hi} rows.
high_score_defaults:
    .byte $53,$49,$58,$48,$01,$01,$44,$4F,$4D,$45,$05
    .byte $50,$52,$49,$FC,$03,$54,$57,$44,$7D,$03
    .byte $54,$41,$4E,$22,$03,$54,$42,$20,$F3,$02
    .byte $41,$43,$45,$8A,$02,$4D,$41,$58,$1C,$02
    .byte $5A,$45,$44,$AE,$01,$42,$4F,$54,$40,$01
    .byte $43,$50,$55,$D2,$00
