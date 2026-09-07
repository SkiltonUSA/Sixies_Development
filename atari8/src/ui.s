.segment "LOGIC"
; Show persistence separately from rank/initials. A failed write never discards
; the in-memory table. Retry uses the same checked SIO path and overwrites the
; full fixed-width status line, leaving no stale failure text behind.
draw_save_status:
    lda high_score_editing
    bne @done                   ; new initials have not been saved yet
    lda high_score_save_status
    beq @done
    cmp #2
    beq @failed
    lda #<ui_saved
    ldx #>ui_saved
    bne @draw
@failed:
    lda high_score_retry_enabled
    beq @session_only
    lda #<ui_session
    ldx #>ui_session
    bne @draw
@session_only:
    lda #<ui_session_only
    ldx #>ui_session_only
@draw:
    sta zp_text
    stx zp_text+1
    lda #164
    ldx #7
    jsr draw_text
@done:
    rts

; Only the post-game score screen owns retry input. Up allows joystick-only
; players to retry after inserting/enabling a writable disk.
wait_for_scores_start:
    jsr wait_action
    cmp #ACTION_PLACE
    beq @done
    cmp #ACTION_NEW
    beq @done
    cmp #ACTION_YES
    beq @done
    cmp #ACTION_RETRY
    beq @retry
    cmp #ACTION_UP
    bne wait_for_scores_start
@retry:
    lda high_score_save_status
    cmp #2
    bne wait_for_scores_start
    jsr high_scores_save
    jsr draw_save_status
    jsr arm_input
    jmp wait_for_scores_start
@done:
    rts

.segment "RODATA"
ui_saved:      .asciiz "          SAVED           "
ui_session:    .asciiz "SESSION ONLY R/UP TO RETRY "
ui_session_only:.asciiz "       SESSION ONLY       "
