// MotoNode controller: drives a daisy chain of WS2815 light modules and
// mirrors the vehicle's brake and turn signals onto them.
#include <Arduino.h>
#include <FastLED.h>
#include <Preferences.h>

#include "config.h"

static CRGB leds[NUM_LEDS];
static Preferences prefs;

enum Effect : uint8_t { FX_SOLID, FX_BREATHE, FX_RAINBOW, FX_CHASE, FX_OFF, FX_COUNT };
static const char *const EFFECT_NAMES[] = {"solid", "breathe", "rainbow", "chase", "off"};

static uint8_t effect = FX_SOLID;
static uint8_t brightnessStep = sizeof(BRIGHTNESS_STEPS) - 1;

// ---------------------------------------------------------------------------
// Inputs
// ---------------------------------------------------------------------------

// Debounced active-low input. update() returns true when the stable state changes.
struct Input {
  uint8_t pin;
  bool active = false;
  bool lastRaw = false;
  uint32_t rawChangedAt = 0;

  void begin(uint8_t p) {
    pin = p;
    pinMode(pin, INPUT_PULLUP);
  }

  bool update(uint32_t now) {
    bool raw = digitalRead(pin) == LOW;
    if (raw != lastRaw) {
      lastRaw = raw;
      rawChangedAt = now;
    }
    if (raw != active && now - rawChangedAt >= DEBOUNCE_MS) {
      active = raw;
      return true;
    }
    return false;
  }
};

// Follows the vehicle's flasher: each "on" pulse restarts the sweep, and the
// side stays engaged through the flasher's off phase so it doesn't fall back
// to the accent effect between blinks.
struct Indicator {
  Input in;
  uint32_t pulseStart = 0;
  uint32_t lastOn = 0;
  bool seen = false;

  void update(uint32_t now) {
    if (in.update(now) && in.active) pulseStart = now;
    if (in.active) {
      lastOn = now;
      seen = true;
    }
  }

  bool engaged(uint32_t now) const {
    return seen && (in.active || now - lastOn < TURN_HOLD_MS);
  }

  // How many LEDs of a module are lit right now (0 during the off phase).
  uint8_t litCount(uint32_t now) const {
    if (!in.active) return 0;
    uint32_t t = now - pulseStart;
    if (t >= SWEEP_MS) return LEDS_PER_MODULE;
    return (t * LEDS_PER_MODULE) / SWEEP_MS + 1;
  }
};

static Input brake;
static Indicator left, right;
static Input button;
static uint32_t buttonDownAt = 0;
static bool longPressFired = false;

static void saveSettings() {
  prefs.putUChar("effect", effect);
  prefs.putUChar("bright", brightnessStep);
}

static void handleButton(uint32_t now) {
  if (button.update(now)) {
    if (button.active) {
      buttonDownAt = now;
      longPressFired = false;
    } else if (!longPressFired) {
      effect = (effect + 1) % FX_COUNT;
      saveSettings();
      Serial.printf("effect -> %s\n", EFFECT_NAMES[effect]);
    }
  }
  if (button.active && !longPressFired && now - buttonDownAt >= LONG_PRESS_MS) {
    longPressFired = true;
    brightnessStep = (brightnessStep + 1) % sizeof(BRIGHTNESS_STEPS);
    saveSettings();
    Serial.printf("brightness -> %u\n", BRIGHTNESS_STEPS[brightnessStep]);
  }
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

// Accent colour for a LED at chain index i. Scaled by the user brightness;
// safety functions (brake, indicators) are not.
static CRGB accentColor(uint16_t i, uint32_t now) {
  CRGB c;
  switch (effect) {
    case FX_SOLID:
      c = COLOR_ACCENT_DEFAULT;
      break;
    case FX_BREATHE:
      c = COLOR_ACCENT_DEFAULT;
      c.nscale8(beatsin8(12, 20, 255));
      break;
    case FX_RAINBOW:
      c = CHSV((now / 16) + i * 8, 255, 255);
      break;
    case FX_CHASE: {
      uint16_t head = (now / 40) % NUM_LEDS;
      uint16_t dist = (i + NUM_LEDS - head) % NUM_LEDS;
      if (dist < 4) {
        c = COLOR_ACCENT_DEFAULT;
        c.nscale8(255 - dist * 60);  // fading tail behind the head
      }
      break;
    }
    default:
      c = CRGB::Black;
  }
  c.nscale8_video(BRIGHTNESS_STEPS[brightnessStep]);
  return c;
}

static void renderModule(uint16_t m, uint32_t now) {
  const ModuleCfg &cfg = MODULES[m];
  CRGB *px = &leds[m * LEDS_PER_MODULE];

  for (uint8_t pos = 0; pos < LEDS_PER_MODULE; pos++) {
    uint8_t phys = cfg.reversed ? LEDS_PER_MODULE - 1 - pos : pos;
    uint16_t chainIndex = m * LEDS_PER_MODULE + phys;
    CRGB c;

    switch (cfg.role) {
      case ROLE_TAIL:
        c = brake.active ? CRGB(255, 0, 0) : CRGB(TAIL_RUNNING_LEVEL, 0, 0);
        break;

      case ROLE_LEFT:
      case ROLE_RIGHT: {
        const Indicator &ind = cfg.role == ROLE_LEFT ? left : right;
        if (ind.engaged(now)) {
          c = pos < ind.litCount(now) ? COLOR_AMBER : CRGB::Black;
        } else {
          c = accentColor(chainIndex, now);
        }
        break;
      }

      default:
        c = accentColor(chainIndex, now);
    }
    px[phys] = c;
  }
}

// Lights each module in turn in its role colour so you can check the chain
// order and spot a dead module at power-up.
static void selfTest() {
  for (uint16_t m = 0; m < NUM_MODULES; m++) {
    CRGB c;
    switch (MODULES[m].role) {
      case ROLE_TAIL: c = CRGB(80, 0, 0); break;
      case ROLE_LEFT:
      case ROLE_RIGHT: c = COLOR_AMBER; c.nscale8(80); break;
      default: c = CRGB(40, 40, 40);
    }
    fill_solid(&leds[m * LEDS_PER_MODULE], LEDS_PER_MODULE, c);
    FastLED.show();
    delay(120);
  }
  delay(300);
  FastLED.clear(true);
}

// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);

  brake.begin(PIN_BRAKE);
  left.in.begin(PIN_LEFT);
  right.in.begin(PIN_RIGHT);
  button.begin(PIN_BUTTON);

  prefs.begin("motonode", false);
  effect = prefs.getUChar("effect", FX_SOLID) % FX_COUNT;
  brightnessStep = prefs.getUChar("bright", brightnessStep) % sizeof(BRIGHTNESS_STEPS);

  FastLED.addLeds<WS2812B, PIN_LED_DATA, GRB>(leds, NUM_LEDS);  // WS2815 uses the WS2812 protocol
  FastLED.setMaxPowerInVoltsAndMilliamps(5, MAX_BUS_MA);         // see MAX_BUS_MA in config.h
  FastLED.setBrightness(255);

  Serial.printf("MotoNode: %u modules, %u LEDs\n", NUM_MODULES, NUM_LEDS);
  selfTest();
}

void loop() {
  static uint32_t lastFrame = 0;
  uint32_t now = millis();

  brake.update(now);
  left.update(now);
  right.update(now);
  handleButton(now);

  if (now - lastFrame < 10) return;  // ~100 fps
  lastFrame = now;

  for (uint16_t m = 0; m < NUM_MODULES; m++) renderModule(m, now);
  FastLED.show();
}
