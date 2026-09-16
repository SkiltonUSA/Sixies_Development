; Keyboard/joystick focus handling for the two controls below the grid.
; The packed merge callouts end at $3ecc; the next fixed UI asset is $41d0.
* = $3ed0

FocusSettingsIcon:
    lda settingsFocused
    bne FocusSettingsIcon_Done
    lda highlightedIndex
    cmp #$ff
    beq FocusSettingsIcon_Set
    jsr ClearCursorHighlights
    lda #$ff
    sta highlightedIndex
    sta highlightedSecondIndex
FocusSettingsIcon_Set:
    lda #1
    sta settingsFocused
    sta ghostSuppressed
    jsr UpdateBottomButtonColors
    jsr MarkDisplayDirty
    jsr PlayBounce
FocusSettingsIcon_Done:
    rts

FocusBottomOption:
    lda cursorX
    cmp #3
    bcc FocusBottomOption_NewGame
    jmp FocusSettingsIcon
FocusBottomOption_NewGame:
    jmp FocusNewGameIcon

HandleBottomControlAction:
    lda newGameFocused
    beq HandleBottomControlAction_Settings
    lda action
    cmp #ACTION_PLACE
    beq HandleBottomControlAction_NewGame
    cmp #ACTION_UP
    beq HandleBottomControlAction_UnfocusNewGame
    cmp #ACTION_RIGHT
    bne HandleBottomControlAction_None
    lda #0
    sta newGameFocused
    jsr UpdateBottomButtonColors
    jsr FocusSettingsIcon
HandleBottomControlAction_None:
    lda #ACTION_NONE
    rts
HandleBottomControlAction_NewGame:
    lda #ACTION_NEW
    rts
HandleBottomControlAction_UnfocusNewGame:
    jsr UnfocusNewGameIcon
    lda #ACTION_NONE
    rts
HandleBottomControlAction_Settings:
    lda action
    cmp #ACTION_PLACE
    beq HandleBottomControlAction_OpenSettings
    cmp #ACTION_UP
    beq HandleBottomControlAction_UnfocusSettings
    cmp #ACTION_LEFT
    bne HandleBottomControlAction_None
    lda #0
    sta settingsFocused
    jsr UpdateBottomButtonColors
    jsr FocusNewGameIcon
    lda #ACTION_NONE
    rts
HandleBottomControlAction_OpenSettings:
    lda #ACTION_SETTINGS
    rts
HandleBottomControlAction_UnfocusSettings:
    jsr UnfocusSettingsIcon
    lda #ACTION_NONE
    rts

FocusNewGameIcon:
    lda newGameFocused
    bne FocusNewGameIcon_Done
    lda highlightedIndex
    cmp #$ff
    beq FocusNewGameIcon_Set
    jsr ClearCursorHighlights
    lda #$ff
    sta highlightedIndex
    sta highlightedSecondIndex
FocusNewGameIcon_Set:
    lda #1
    sta newGameFocused
    sta ghostSuppressed
    jsr UpdateBottomButtonColors
    jsr MarkDisplayDirty
    jsr PlayBounce
FocusNewGameIcon_Done:
    rts

UnfocusSettingsIcon:
    lda #0
    sta settingsFocused
    beq UnfocusBottomIcon

UnfocusNewGameIcon:
    lda #0
    sta newGameFocused
UnfocusBottomIcon:
    sta ghostSuppressed
    jsr UpdateBottomButtonColors
    jsr UpdatePlacement
    jsr BuildDisplayBoard
    jsr UpdateCursorHighlight
    jsr PlayBounce
    rts

; Audio entry-point wrappers make the selected settings mode global without
; adding checks to every gameplay call site.
PlayBounce:
    lda audioMode
    and #1
    bne AudioDisabledReturn
    jsr PlayBounceImpl
    jmp RetriggerAndApplySoundEffectVoice

PlayPortalPing:
    lda audioMode
    and #1
    bne AudioDisabledReturn
    jsr PlayPortalPingImpl
    jmp RetriggerAndApplySoundEffectVoice

PlayGridSetup:
    lda audioMode
    and #1
    bne AudioDisabledReturn
    jsr PlayGridSetupImpl
    jmp RetriggerAndApplySoundEffectVoice

PlayInvalidPlacement:
    lda audioMode
    and #1
    bne AudioDisabledReturn
    jsr PlayInvalidPlacementImpl
    jmp RetriggerAndApplySoundEffectVoice

PlayFirstMerge:
    lda audioMode
    and #1
    bne AudioDisabledReturn
    jmp PlayFirstMergeImpl

PlaySecondMerge:
    lda audioMode
    and #1
    bne AudioDisabledReturn
    jmp PlaySecondMergeImpl

InitTitleMusic:
    lda audioMode
    and #2
    beq InitTitleMusic_Enabled
    jsr ResetSoundEffects
    jmp StopTitleMusic
InitTitleMusic_Enabled:
    lda titleMusicActive
    bne AudioDisabledReturn
    jmp InitTitleMusicImpl

; Title, attract, and game-over presentation always restart the tune. The
; gameplay preference is reapplied when the player begins or resumes a game.
InitAttractMusic:
    jsr StopTitleMusic
    jmp InitTitleMusicImpl

AudioDisabledReturn:
    rts

DrawSettingsArtwork:
    lda #<SettingsDiceBitmapData
    sta SOURCE_LO
    lda #>SettingsDiceBitmapData
    sta SOURCE_HI
    lda #1
    sta workRow
DrawSettingsArtwork_BitmapRow:
    lda workRow
    jsr SetBitmapRowPointer
    lda #1
    jsr AddColumnOffset
    ldy #0
DrawSettingsArtwork_BitmapByte:
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    cpy #64
    bne DrawSettingsArtwork_BitmapByte
    lda SOURCE_LO
    clc
    adc #64
    sta SOURCE_LO
    bcc DrawSettingsArtwork_BitmapSourceReady
    inc SOURCE_HI
DrawSettingsArtwork_BitmapSourceReady:
    inc workRow
    lda workRow
    cmp #8
    bne DrawSettingsArtwork_BitmapRow

    lda #<SettingsDiceScreenData
    sta SOURCE_LO
    lda #>SettingsDiceScreenData
    sta SOURCE_HI
    lda #1
    sta workRow
DrawSettingsArtwork_ScreenRow:
    lda workRow
    jsr SetScreenRowPointer
    inc PTR_LO
    bne DrawSettingsArtwork_ScreenReady
    inc PTR_HI
DrawSettingsArtwork_ScreenReady:
    ldy #0
DrawSettingsArtwork_ScreenByte:
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    cpy #8
    bne DrawSettingsArtwork_ScreenByte
    lda SOURCE_LO
    clc
    adc #8
    sta SOURCE_LO
    bcc DrawSettingsArtwork_ScreenSourceReady
    inc SOURCE_HI
DrawSettingsArtwork_ScreenSourceReady:
    inc workRow
    lda workRow
    cmp #8
    bne DrawSettingsArtwork_ScreenRow
    rts

; Start with effects enabled and gameplay music muted. Attract music is always on.
audioMode: !byte AUDIO_SFX_ONLY

WaitForSettingsClose:
    jsr SettingsReleaseInput
WaitForSettingsClose_Frame:
    jsr WaitFrame
    jsr SCNKEY
WaitForSettingsClose_ReadKey:
    jsr GETIN
    beq SettingsReadJoystick
    cmp #'1'
    beq SettingsChooseOne
    cmp #'2'
    beq SettingsChooseTwo
    cmp #'3'
    beq SettingsChooseThree
    cmp #'W'
    bne WaitForSettingsClose_CheckDown
    jmp SettingsMoveUp
WaitForSettingsClose_CheckDown:
    cmp #'S'
    bne WaitForSettingsClose_CheckMenu
    jmp SettingsMoveDown
WaitForSettingsClose_CheckMenu:
    cmp #'M'
    bne WaitForSettingsClose_CheckClose
    jmp SettingsReturnMenu
WaitForSettingsClose_CheckClose:
    cmp #'X'
    bne WaitForSettingsClose_CheckSpace
    jmp SettingsClose
WaitForSettingsClose_CheckSpace:
    cmp #' '
    bne WaitForSettingsClose_CheckReturn
    jmp SettingsSelect
WaitForSettingsClose_CheckReturn:
    cmp #13
    bne WaitForSettingsClose_NoKey
    jmp SettingsSelect
WaitForSettingsClose_NoKey:
    jmp WaitForSettingsClose_Frame

SettingsReadJoystick:
    lda JOYSTICK2
    and #$1f
    cmp #$1f
    bne SettingsJoystickPressed
    lda #0
    sta joystickLatch
    beq WaitForSettingsClose_Frame
SettingsJoystickPressed:
    lda joystickLatch
    bne WaitForSettingsClose_Frame
    inc joystickLatch
    lda JOYSTICK2
    and #$01
    beq SettingsMoveUp
    lda JOYSTICK2
    and #$02
    beq SettingsMoveDown
    lda JOYSTICK2
    and #$10
    bne SettingsJoystickUnhandled
    jmp SettingsSelect
SettingsJoystickUnhandled:
    bne WaitForSettingsClose_Frame

SettingsChooseOne:
    lda #0
    beq SettingsChooseNumber
SettingsChooseTwo:
    lda #1
    bne SettingsChooseNumber
SettingsChooseThree:
    lda #2
SettingsChooseNumber:
    ldx settingsPage
    cpx #3
    beq SettingsChooseAudio
    cpx #0
    beq SettingsChoosePage
    jmp SettingsIgnoreInput
SettingsChoosePage:
    clc
    adc #1
    sta settingsPage
    jmp SettingsRedraw
SettingsChooseAudio:
    cmp #2
    bcs SettingsIgnoreInput
    sta settingsOptionSelection
    jmp SettingsApplyAudio
SettingsIgnoreInput:
    jmp WaitForSettingsClose_Frame

SettingsMoveUp:
    lda settingsPage
    beq SettingsMoveUpMenu
    cmp #3
    bne SettingsIgnoreInput
    lda settingsOptionSelection
    beq SettingsMoveUpAudioWrap
    dec settingsOptionSelection
    jmp SettingsRedraw
SettingsMoveUpAudioWrap:
    lda #1
    sta settingsOptionSelection
    bne SettingsRedraw
SettingsMoveUpMenu:
    lda settingsMenuSelection
    beq SettingsMoveUpMenuWrap
    dec settingsMenuSelection
    jmp SettingsRedraw
SettingsMoveUpMenuWrap:
    lda #2
    sta settingsMenuSelection
    bne SettingsRedraw

SettingsMoveDown:
    lda settingsPage
    beq SettingsMoveDownMenu
    cmp #3
    bne SettingsIgnoreInput
    inc settingsOptionSelection
    lda settingsOptionSelection
    cmp #2
    bcc SettingsRedraw
    lda #0
    sta settingsOptionSelection
    beq SettingsRedraw
SettingsMoveDownMenu:
    inc settingsMenuSelection
    lda settingsMenuSelection
    cmp #3
    bcc SettingsRedraw
    lda #0
    sta settingsMenuSelection
    beq SettingsRedraw

SettingsSelect:
    lda settingsPage
    beq SettingsOpenMenuChoice
    cmp #3
    bne SettingsReturnMenu
    jmp SettingsApplyAudio
SettingsReturnMenu:
    lda #0
    sta settingsPage
    beq SettingsRedraw
SettingsOpenMenuChoice:
    lda settingsMenuSelection
    clc
    adc #1
    sta settingsPage
    bne SettingsRedraw

SettingsRedraw:
    sei
    jsr ClearBitmap
    jsr InitScreenColors
    jsr DrawSettingsText
    cli
    jsr SettingsReleaseInput
    jmp WaitForSettingsClose_Frame

SettingsReleaseInput:
    jsr SCNKEY
    lda KEY_CURRENT
    cmp #$40
    bne SettingsReleaseInput
    jsr GETIN
    bne SettingsReleaseInput
    lda JOYSTICK2
    and #$1f
    cmp #$1f
    bne SettingsReleaseInput
    lda #0
    sta joystickLatch
    sta joystickFireState
    rts

SettingsClose:
    jsr SettingsReleaseInput
    rts
