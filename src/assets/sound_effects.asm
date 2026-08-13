; Compact SID effects used by movement, placement, and board setup.
* = $8f00

ResetSoundEffects:
    lda #0
    sta sfxFrames
    sta sfxPriority
    sta sfxGateOffControl
    sta sfxMode
    sta sfxRandomCounter
    sta sfxSweepLo
    sta sfxSweepHi
    sta SID_V1_CONTROL
    sta SID_V1_FREQ_LO
    sta SID_V1_FREQ_HI
    sta SID_V1_PW_LO
    sta SID_V1_PW_HI
    sta SID_V1_AD
    sta SID_V1_SR
    lda #$0f
    sta SID_MODE_VOLUME
    lda #$a5
    sta sfxRandomSeed
    rts

PlayBounce:
    lda sfxPriority
    cmp #2
    bcs PlayBounce_Done
    lda #1
    sta sfxPriority
    lda #0
    sta sfxMode
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
    lda #0
    sta sfxMode
    lda #5
    sta sfxFrames
    rts

PlayGridSetup:
    jsr InitTest11
    lda #3
    sta sfxPriority
    lda #34
    sta sfxFrames
    rts

PlayInvalidPlacement:
    jsr InitInvalidBonk
    lda #2
    sta sfxPriority
    lda #9
    sta sfxFrames
    rts

PlayFirstMerge:
    ; A rising major arpeggio gives every first merge a happy resolution.
    lda #$40
    sta SID_V1_CONTROL
    sta sfxGateOffControl
    lda #$67
    sta SID_V1_FREQ_LO
    lda #$11
    sta SID_V1_FREQ_HI
    lda #0
    sta SID_V1_PW_LO
    lda #$08
    sta SID_V1_PW_HI
    lda #$02
    sta SID_V1_AD
    lda #$a3
    sta SID_V1_SR
    lda #$41
    sta SID_V1_CONTROL
    lda #3
    sta sfxPriority
    sta sfxMode
    lda #16
    sta sfxFrames
    rts

PlaySecondMerge:
    ; A brighter octave-up flourish distinguishes the second chain reaction.
    lda #$40
    sta SID_V1_CONTROL
    sta sfxGateOffControl
    lda #$ce
    sta SID_V1_FREQ_LO
    lda #$22
    sta SID_V1_FREQ_HI
    lda #0
    sta SID_V1_PW_LO
    lda #$06
    sta SID_V1_PW_HI
    lda #$01
    sta SID_V1_AD
    lda #$b4
    sta SID_V1_SR
    lda #$41
    sta SID_V1_CONTROL
    lda #4
    sta sfxPriority
    sta sfxMode
    lda #20
    sta sfxFrames
    rts

InitTest11:
    ; Recreate the Sound FX Kit TEST11 patch shown in the reference image.
    ; Its RANDOM option modulates the displayed $b105 sawtooth frequency.
    lda #$20
    sta SID_V1_CONTROL
    sta sfxGateOffControl
    lda #$05
    sta SID_V1_FREQ_LO
    lda #$b1
    sta SID_V1_FREQ_HI
    lda #0
    sta SID_V1_PW_LO
    sta SID_V1_PW_HI
    sta sfxRandomCounter
    lda #$74
    sta SID_V1_AD
    lda #$2a
    sta SID_V1_SR
    lda rngSeed
    eor frameCounter
    ora #1
    sta sfxRandomSeed
    lda #$21
    sta SID_V1_CONTROL
    lda #1
    sta sfxMode
    lda #5
    sta sfxRandomFloor
    lda #173
    sta sfxRandomRange
    lda #2
    sta sfxRandomPeriod
    rts

InitInvalidBonk:
    ; A low triangle "bonk" that falls from about 300 Hz to 120 Hz.
    lda #$10
    sta SID_V1_CONTROL
    sta sfxGateOffControl
    lda #$00
    sta sfxSweepLo
    sta SID_V1_FREQ_LO
    sta SID_V1_PW_LO
    sta SID_V1_PW_HI
    lda #$14
    sta sfxSweepHi
    sta SID_V1_FREQ_HI
    lda #$03
    sta SID_V1_AD
    lda #$23
    sta SID_V1_SR
    lda #$11
    sta SID_V1_CONTROL
    lda #2
    sta sfxMode
    rts

StopGridSetup:
    lda sfxMode
    beq StopGridSetup_Done
    lda sfxGateOffControl
    sta SID_V1_CONTROL
    lda #0
    sta sfxFrames
    sta sfxPriority
    sta sfxMode
StopGridSetup_Done:
    rts

UpdateSoundEffects:
    lda sfxFrames
    beq UpdateSoundEffects_Done
    lda sfxMode
    beq UpdateSoundEffects_Tick
    cmp #1
    beq UpdateSoundEffects_GridSetup
    cmp #2
    beq UpdateSoundEffects_Invalid
    cmp #3
    beq UpdateSoundEffects_FirstMerge
    cmp #4
    beq UpdateSoundEffects_SecondMerge
    cmp #8
    beq UpdateSoundEffects_SixMerge
    jsr UpdateHigherMergeNotes
    jmp UpdateSoundEffects_Tick
UpdateSoundEffects_SixMerge:
    jsr UpdateSixMergeExplosion
    jmp UpdateSoundEffects_Tick
UpdateSoundEffects_SecondMerge:
    jsr UpdateSecondMergeNotes
    jmp UpdateSoundEffects_Tick
UpdateSoundEffects_FirstMerge:
    jsr UpdateFirstMergeNotes
    jmp UpdateSoundEffects_Tick
UpdateSoundEffects_GridSetup:
    jsr UpdateGridSetupPitch
    jmp UpdateSoundEffects_Tick
UpdateSoundEffects_Invalid:
    jsr UpdateInvalidPlacementPitch
UpdateSoundEffects_Tick:
    dec sfxFrames
    bne UpdateSoundEffects_Done
    lda sfxGateOffControl
    sta SID_V1_CONTROL
    lda #0
    sta sfxPriority
    sta sfxMode
UpdateSoundEffects_Done:
    rts

UpdateGridSetupPitch:
    ; The per-patch period and bounds reproduce the selected random mode while
    ; keeping the 8-bit Galois LFSR cheap enough for the lower-border IRQ.
    inc sfxRandomCounter
    lda sfxRandomCounter
    cmp sfxRandomPeriod
    bcc UpdateGridSetupPitch_Done
    lda #0
    sta sfxRandomCounter
    lda sfxRandomSeed
    lsr
    bcc UpdateGridSetupPitch_StoreSeed
    eor #$b8
UpdateGridSetupPitch_StoreSeed:
    sta sfxRandomSeed
    cmp sfxRandomRange
    bcc UpdateGridSetupPitch_InRange
    sec
    sbc sfxRandomRange
UpdateGridSetupPitch_InRange:
    clc
    adc sfxRandomFloor
    sta SID_V1_FREQ_HI
UpdateGridSetupPitch_Done:
    rts

UpdateInvalidPlacementPitch:
    sec
    lda sfxSweepLo
    sbc #$50
    sta sfxSweepLo
    sta SID_V1_FREQ_LO
    lda sfxSweepHi
    sbc #1
    sta sfxSweepHi
    sta SID_V1_FREQ_HI
    rts

UpdateFirstMergeNotes:
    lda sfxFrames
    cmp #12
    beq UpdateFirstMergeNotes_E
    cmp #8
    beq UpdateFirstMergeNotes_G
    cmp #4
    beq UpdateFirstMergeNotes_HighC
    rts

UpdateFirstMergeNotes_E:
    lda #$ee
    ldx #$15
    bne UpdateFirstMergeNotes_Retrigger
UpdateFirstMergeNotes_G:
    lda #$16
    ldx #$1a
    bne UpdateFirstMergeNotes_Retrigger
UpdateFirstMergeNotes_HighC:
    lda #$ce
    ldx #$22
UpdateFirstMergeNotes_Retrigger:
    pha
    lda #$40
    sta SID_V1_CONTROL
    pla
    sta SID_V1_FREQ_LO
    stx SID_V1_FREQ_HI
    lda #$41
    sta SID_V1_CONTROL
    rts

UpdateSecondMergeNotes:
    lda sfxFrames
    cmp #15
    beq UpdateSecondMergeNotes_E
    cmp #10
    beq UpdateSecondMergeNotes_G
    cmp #5
    beq UpdateSecondMergeNotes_HighC
    rts

UpdateSecondMergeNotes_E:
    lda #$dc
    ldx #$2b
    bne UpdateSecondMergeNotes_Retrigger
UpdateSecondMergeNotes_G:
    lda #$2c
    ldx #$34
    bne UpdateSecondMergeNotes_Retrigger
UpdateSecondMergeNotes_HighC:
    lda #$9c
    ldx #$45
UpdateSecondMergeNotes_Retrigger:
    pha
    lda #$40
    sta SID_V1_CONTROL
    pla
    sta SID_V1_FREQ_LO
    stx SID_V1_FREQ_HI
    lda #$41
    sta SID_V1_CONTROL
    rts

sfxFrames:         !byte 0
sfxPriority:       !byte 0
sfxGateOffControl: !byte 0
sfxMode:           !byte 0
sfxRandomSeed:     !byte $a5
sfxRandomCounter:  !byte 0
sfxRandomFloor:    !byte 0
sfxRandomRange:    !byte 1
sfxRandomPeriod:   !byte 1
sfxSweepLo:        !byte 0
sfxSweepHi:        !byte 0
