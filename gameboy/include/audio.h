#ifndef SIXIES_AUDIO_H
#define SIXIES_AUDIO_H

#include <gb/gb.h>

extern uint8_t audio_enabled;
void audio_initialize(void);
void audio_scene_load_begin(void);
void audio_scene_load_end(void);
void music_start(void) NONBANKED;
void music_stop(void) NONBANKED;
void music_tick(void) NONBANKED;

#endif
