; One-button joystick chord support, fitted into two gaps around title music.
; Fire alone places on release. Fire+left/right rotates once per direction press.
* = $96e8

HandleJoystickFireRelease:
    lda joystickFireState
    beq HandleJoystickFireRelease_NotHandled
    tax
    lda #0
    sta joystickFireState
    dex
    bne HandleJoystickFireRelease_Handled
    lda #ACTION_PLACE
    sta action
HandleJoystickFireRelease_Handled:
    sec
    rts
HandleJoystickFireRelease_NotHandled:
    jmp ReadAction_Joystick_Normal

* = $9777

PollGameplayJoystickChord:
    lda JOYSTICK2
    and #$10
    beq PollGameplayJoystickChord_FireHeld
    jmp HandleJoystickFireRelease

PollGameplayJoystickChord_FireHeld:
    lda joystickFireState
    bne PollGameplayJoystickChord_StateReady
    inc joystickFireState
PollGameplayJoystickChord_StateReady:
    lda pieceCount
    cmp #2
    bne PollGameplayJoystickChord_Rearm
    lda JOYSTICK2
    and #$04
    beq PollGameplayJoystickChord_Left
    lda JOYSTICK2
    and #$08
    beq PollGameplayJoystickChord_Right
PollGameplayJoystickChord_Rearm:
    lda #0
    sta joystickLatch
    sec
    rts

PollGameplayJoystickChord_Left:
    ldy #ACTION_ROTATE_LEFT
    bne PollGameplayJoystickChord_Rotate
PollGameplayJoystickChord_Right:
    ldy #ACTION_ROTATE
PollGameplayJoystickChord_Rotate:
    ldx joystickLatch
    bne PollGameplayJoystickChord_Handled
    inc joystickLatch
    lda #2
    sta joystickFireState
    sty action
PollGameplayJoystickChord_Handled:
    sec
    rts
