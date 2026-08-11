; Compact bounce and portal_ping presets reproduced from c64SIDkit.
* = $8f00

ResetSoundEffects:
    lda #0
    sta sfxFrames
    sta sfxPriority
    sta sfxGateOffControl
    sta SID_V1_CONTROL
    sta SID_V1_FREQ_LO
    sta SID_V1_FREQ_HI
    sta SID_V1_PW_LO
    sta SID_V1_PW_HI
    sta SID_V1_AD
    sta SID_V1_SR
    lda #$0f
    sta SID_MODE_VOLUME
    rts

PlayBounce:
    lda sfxPriority
    cmp #2
    bcs PlayBounce_Done
    lda #1
    sta sfxPriority
    lda #$20
    sta SID_V1_CONTROL
    sta sfxGateOffControl
    lda #$00
    sta SID_V1_FREQ_LO
    sta SID_V1_PW_LO
    sta SID_V1_PW_HI
    sta SID_V1_AD
    sta SID_V1_SR
    lda #$30
    sta SID_V1_FREQ_HI
    lda #$21
    sta SID_V1_CONTROL
    lda #3
    sta sfxFrames
PlayBounce_Done:
    rts

PlayPortalPing:
    ; Drop the previous gate before restoring the preset registers so rapid
    ; rotations retrigger the envelope instead of extending the old note.
    lda #$10
    sta SID_V1_CONTROL
    sta sfxGateOffControl
    lda #$00
    sta SID_V1_FREQ_LO
    sta SID_V1_PW_LO
    sta SID_V1_PW_HI
    sta SID_V1_SR
    lda #$20
    sta SID_V1_FREQ_HI
    lda #$02
    sta SID_V1_AD
    lda #$11
    sta SID_V1_CONTROL
    lda #2
    sta sfxPriority
    lda #5
    sta sfxFrames
    rts

UpdateSoundEffects:
    lda sfxFrames
    beq UpdateSoundEffects_Done
    dec sfxFrames
    bne UpdateSoundEffects_Done
    lda sfxGateOffControl
    sta SID_V1_CONTROL
    lda #0
    sta sfxPriority
UpdateSoundEffects_Done:
    rts

sfxFrames:         !byte 0
sfxPriority:       !byte 0
sfxGateOffControl: !byte 0
