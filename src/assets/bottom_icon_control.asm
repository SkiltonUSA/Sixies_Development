; The compact Chain Reaction sprite leaves this persistent-data gap available
; for the two dynamic Sound FX option labels.
* = $5ac0

SettingsTextSoundFxOn:  !text "2. SOUND FX: ON "
SettingsTextSoundFxOff: !text "2. SOUND FX: OFF"

; The imported player writes directly to $d400-$d418. Run it briefly with I/O
; hidden so those writes land in the RAM underneath, copy the resulting state,
; then publish all 25 registers to the real SID. This gives gameplay effects a
; reliable music state to cover and lets the tune reclaim voice 1 immediately
; after an effect, including pulse width and envelope registers that a player
; does not necessarily rewrite every frame.
* = $5ae0

RunTitleMusicInitShadowed:
    pha
    lda #$30
    sta CPU_PORT
    pla
    jsr TITLE_MUSIC_INIT
    jmp PublishTitleMusicShadow

RunTitleMusicPlayShadowed:
    lda #$30
    sta CPU_PORT
    jsr TITLE_MUSIC_PLAY

PublishTitleMusicShadow:
    ldx #24
PublishTitleMusicShadow_Capture:
    lda $d400,x
    sta titleMusicSidShadow,x
    dex
    bpl PublishTitleMusicShadow_Capture
    lda #$36
    sta CPU_PORT
    ldx #24
PublishTitleMusicShadow_Register:
    lda titleMusicSidShadow,x
    sta $d400,x
    dex
    bpl PublishTitleMusicShadow_Register
    rts

titleMusicSidShadow: !fill 25,0

SettingsTextMusicOn:  !text "1. MUSIC: ON "
SettingsTextMusicOff: !text "1. MUSIC: OFF"

SelectAudioOptionText:
    lda audioMode
    and #2
    bne SelectAudioOptionText_MusicOff
    lda #<SettingsTextMusicOn
    ldx #>SettingsTextMusicOn
    bne SelectAudioOptionText_StoreMusic
SelectAudioOptionText_MusicOff:
    lda #<SettingsTextMusicOff
    ldx #>SettingsTextMusicOff
SelectAudioOptionText_StoreMusic:
    sta SettingsLineLo + 23
    stx SettingsLineHi + 23

    lda audioMode
    and #1
    bne SelectAudioOptionText_SoundFxOff
    lda #<SettingsTextSoundFxOn
    ldx #>SettingsTextSoundFxOn
    bne SelectAudioOptionText_StoreSoundFx
SelectAudioOptionText_SoundFxOff:
    lda #<SettingsTextSoundFxOff
    ldx #>SettingsTextSoundFxOff
SelectAudioOptionText_StoreSoundFx:
    sta SettingsLineLo + 24
    stx SettingsLineHi + 24
    rts

; Configure the original controls for side-panel display after the
; upcoming-piece preview has finished. The former bitmap-button color helper
; left this verified register-setup gap available.
* = $5980

ConfigureBottomIcons:
    jsr ConfigureNewGameSprite
    lda #$77
    sta SPRITE0_PTR + 7
    lda settingsFocused
    beq ConfigureBottomIcons_SettingsIdle
    lda #COLOR_YELLOW
    bne ConfigureBottomIcons_SettingsColor
ConfigureBottomIcons_SettingsIdle:
    lda #COLOR_LTBLUE
ConfigureBottomIcons_SettingsColor:
    sta SPRITE0_COLOR + 7
    lda #SETTINGS_ICON_X
    sta SPRITE0_X + 14
    lda #SIDE_CONTROL_ICON_Y
    sta SPRITE0_Y + 14
    rts

; Chain-reaction effect code ends below this address; the hand-authored bottom
; controls begin at $3ed0. Keep scheduling logic here so the tightly packed
; game-over tables and firework paths around $5980 do not need to move.
* = $3d20

SettingsApplyAudio:
    lda settingsOptionSelection
    bne SettingsToggleSoundFx
SettingsToggleMusic:
    lda audioMode
    eor #2
    sta audioMode
    and #2
    bne SettingsToggleMusic_Disabled
    jsr InitTitleMusic
    jmp SettingsRedraw
SettingsToggleMusic_Disabled:
    jsr StopTitleMusic
    jmp SettingsRedraw

SettingsToggleSoundFx:
    lda audioMode
    eor #1
    sta audioMode
    and #1
    bne SettingsToggleSoundFx_Disabled
    jmp SettingsRedraw
SettingsToggleSoundFx_Disabled:
    jsr ResetSoundEffects
    jmp SettingsRedraw

; SID write registers cannot be read reliably on real hardware, so effects
; keep their complete voice-1 state here. The gameplay IRQ calls this after
; the music player, allowing an active effect to borrow voice 1 while the tune
; continues uninterrupted on voices 2-3.
ApplySoundEffectVoice:
    ldx #6
ApplySoundEffectVoice_Register:
    lda sfxVoice1Shadow,x
    sta SID_HW_V1_FREQ_LO,x
    dex
    bpl ApplySoundEffectVoice_Register
    rts

sfxVoice1Shadow: !fill 7,0

* = $3d80

SetupBottomSpritesImpl:
    lda titleScreenActive
    bne SetupBottomSpritesImpl_Return
    lda fireworkActive
    ; Value 1 is the single-sprite score flight, which can share the raster
    ; with both controls. Value 2 means the particle burst owns sprites 5-7;
    ; do not replace any of their pointers or coordinates with icon state.
    cmp #2
    beq SetupBottomSpritesImpl_Return
    lda fireworkActive
    bne SetupBottomSpritesImpl_Visible
    lda gameOverBlindActive
    beq SetupBottomSpritesImpl_Visible
    lda #0
    sta uiEnableMask
    sta SPRITE_ENABLE
SetupBottomSpritesImpl_Return:
    rts

SetupBottomSpritesImpl_Visible:
    jsr ConfigureBottomIcons
    ; Merge effects stay left of X=256; only the Settings icon needs its MSB.
    lda #%10000000
    sta SPRITE_X_MSB
    ; Sprite 5 carries the floating merge score/effect above this raster line.
    ; Preserve its expansion while returning sprites 6-7 to control-icon size.
    lda SPRITE_X_EXPAND
    and #%00100000
    sta SPRITE_X_EXPAND
    lda SPRITE_Y_EXPAND
    and #%00100000
    sta SPRITE_Y_EXPAND
    lda #%11000000
    ldx fireworkActive
    beq SetupBottomSpritesImpl_MaskReady
    ora #%00100000
SetupBottomSpritesImpl_MaskReady:
    sta uiEnableMask
    jmp EnableBottomSprites
