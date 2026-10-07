#pragma once
#include <stdint.h>

// ---------------------------------------------------------------------------
// Chain layout. Edit this to match your build.
// ---------------------------------------------------------------------------
#define LEDS_PER_MODULE 8

enum Role : uint8_t {
  ROLE_ACCENT,  // runs the selected effect
  ROLE_LEFT,    // amber sequential sweep with the left indicator, accent otherwise
  ROLE_RIGHT,   // amber sequential sweep with the right indicator, accent otherwise
  ROLE_TAIL,    // dim red running light, full red on brake
};

struct ModuleCfg {
  Role role;
  bool reversed;  // flip LED order so sweeps run outward regardless of mounting
};

// One entry per module, in chain order (module 1 is nearest the controller).
static const ModuleCfg MODULES[] = {
    {ROLE_LEFT, true},
    {ROLE_ACCENT, false},
    {ROLE_TAIL, false},
    {ROLE_TAIL, false},
    {ROLE_ACCENT, false},
    {ROLE_RIGHT, false},
};

static const uint16_t NUM_MODULES = sizeof(MODULES) / sizeof(MODULES[0]);
static const uint16_t NUM_LEDS = NUM_MODULES * LEDS_PER_MODULE;

// ---------------------------------------------------------------------------
// Pins (ESP32-C3 SuperMini). Avoid GPIO2/8/9, which are boot strapping pins.
// ---------------------------------------------------------------------------
#define PIN_LED_DATA 10
#define PIN_BRAKE 5   // active low (PC817 pulls low when 12 V present)
#define PIN_LEFT 6
#define PIN_RIGHT 7
#define PIN_BUTTON 4  // to GND

// ---------------------------------------------------------------------------
// Behaviour
// ---------------------------------------------------------------------------
// Bus current budget. WS2815 draws about the same current per channel at 12 V
// as WS2812B does at 5 V, so FastLED's 5 V power model gives the right amps
// when we tell it "5 V" here, even though the bus runs at 12 V.
#define MAX_BUS_MA 1500

#define TAIL_RUNNING_LEVEL 40   // 0-255 red level when not braking (0 = off)
#define SWEEP_MS 350            // time for an indicator sweep to fill a module
#define TURN_HOLD_MS 700        // longer than the flasher's off-time (~330-500 ms)
#define DEBOUNCE_MS 15
#define LONG_PRESS_MS 1000

// Warm amber. Pure FastLED "Orange" looks yellow-green on WS2815.
#define COLOR_AMBER CRGB(255, 90, 0)
#define COLOR_ACCENT_DEFAULT CRGB(255, 120, 20)

static const uint8_t BRIGHTNESS_STEPS[] = {64, 128, 255};
