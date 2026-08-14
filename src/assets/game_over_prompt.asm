; Generated from src/assets/font/SixiesFont_image.asm.
; Full-width end-screen prompt rendered with the default Sixies font.
* = $41d0
GameOverPromptText: !text "PRESS N FOR NEW GAME"

DrawGameOverPrompt:
    lda #<GameOverPromptText
    ldx #>GameOverPromptText
    jsr SetHighScoreTextSource
    lda #20
    sta highTextLength
    lda #23
    sta highTextRow
    lda #0
    sta highTextColumn
    lda #COLOR_WHITE
    sta highTextColor
    jmp DrawSixiesMulticolorText
