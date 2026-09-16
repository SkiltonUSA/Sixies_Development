#ifndef SIXIES_EFFECTS_H
#define SIXIES_EFFECTS_H

#include <stdint.h>

void effects_present_merge(
    uint8_t consumed_face,
    uint8_t group_count,
    uint8_t origin,
    uint8_t chain_depth,
    uint16_t award,
    uint8_t callout
);

#endif
