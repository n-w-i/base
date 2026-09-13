# Base

A performance coach that reads my WHOOP data alongside my calendar and tells me
something useful about tomorrow. It runs entirely on my own machine — my health
data never leaves the laptop.

Seven modules that each run on their own or together. Here's the whole thing
start to finish, in the order I actually did it.

## 1. What I wanted

WHOOP is really good at telling you about today and the past. What it never does
is look *forward* — it reports, it doesn't forecast. So the thing I actually
wanted didn't exist: something that knows both how recovered I am *and* what's in
my diary, and puts those two together.

The output I was after is stuff like:

- **"Leg day tomorrow looks good — your HRV is trending up and you slept 8.1h"**
- **"Interview Thursday after Wednesday drinks = risky. Consider skipping the drinks or going easy"**
- **"You need to be asleep by 10:15pm to hit your sleep need before tomorrow's 7am meeting"**
- Dimming the lights when it's time to wind down

## 2. Keeping it on my own machine

This was the constraint everything else got built around. It's my **health data**
— sleep, heart rate, recovery, and my entire calendar. I didn't want any of that
sitting on somebody else's server.

So everything is local:

- All data stored in SQLite (`~/.base/whoop.db`)
- OAuth tokens in the system keychain, not a config file
- APIs bind to `127.0.0.1` only
- No cloud services, no telemetry, no data sharing
- Calendar scanning uses local keyword matching — **event titles never leave the
  machine**, which mattered to me more than the rest of it

It's built to be self-hosted rather than run as a service. Every install is
independent and uses its own credentials, so if a friend also wears WHOOP they
run their own copy the same way. There's no shared server for me to accidentally
become responsible for.

## 3. Breaking it into modules

I built it as seven modules that each run independently or together, rather than
one big program. Each one owns a job and a port, and talks to the others over a
local REST API.

| Module | What it does | Status |
|--------|-------------|--------|
| [whoop-core](./whoop-core/) | OAuth, data sync, local REST API | ✅ Built |
| [calendar-intel](./calendar-intel/) | Reads Google Calendar, classifies events, forecasts | ✅ Built |
| [hevy-intel](./hevy-intel/) | Syncs Hevy workouts, derives per-muscle-group fatigue (optional, needs Hevy Pro) | ✅ Built |
| [recovery-forecast](./recovery-forecast/) | Multi-day recovery prediction model | ✅ Built |
| [base-menubar](./base-menubar/) | macOS menu bar widget (Swift) | ✅ Built |
| [alerts](./alerts/) | Proactive macOS notifications (recovery, risky days, bedtime) | ✅ Built |
| [lights-bridge](./lights-bridge/) | Smart light dimming at wind-down time | ✅ Built |

The three at the top pull data in. Those all feed `recovery-forecast`, which is
the part that does the thinking. Then three things sit on the end and surface it:
the menu bar widget, the alerts, and the lights.

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Google Calendar │     │    WHOOP API     │     │   Hevy API   │
└────────┬────────┘     └────────┬─────────┘     └──────┬───────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  calendar-intel │     │   whoop-core     │     │  hevy-intel  │
│   :9121         │     │   :9120          │     │   :9123      │
└────────┬────────┘     └────────┬─────────┘     └──────┬───────┘
         │                       │                       │
         └───────────┬───────────┴───────────────────────┘
                     ▼
          ┌─────────────────────┐
          │  recovery-forecast  │
          │       :9122         │
          └──────────┬──────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
┌──────────────┐ ┌────────┐ ┌──────────────┐
│ base-menubar │ │ alerts │ │ lights-bridge│
└──────────────┘ └────────┘ └──────────────┘
```

hevy-intel is optional — everything upstream and downstream of it works fine
without a Hevy Pro subscription.

## 4. The forecast, and being honest about it

This is the module I'm most careful about describing.

Your **current** recovery, strain, HRV and sleep are real — straight from WHOOP's
own sensors, unmodified.

Everything about *future* days is **a guess Base makes, not WHOOP** (WHOOP itself
never forecasts, only reports on today and the past). That guess is built from my
real training history plus my calendar, using a "fitness vs. fatigue" model
borrowed from sports science — the same idea tools like TrainingPeaks use.

It is **not machine learning, and it is not validated against my actual
outcomes.** It's a model with assumptions in it, and I'd rather say that plainly
than let it look more authoritative than it is. Full plain-language breakdown of
exactly how it's calculated:
[recovery-forecast/README.md](./recovery-forecast/).

## 5. Making it optional where it needs to be

**hevy-intel** syncs my Hevy workouts and derives per-muscle-group fatigue from
them, so "can I train legs tomorrow" has an actual answer rather than a general
one. But it needs Hevy Pro, which not everyone has, so everything upstream and
downstream of it works fine without it — see
[hevy-intel/README.md](./hevy-intel/).

Same principle for **lights-bridge**, which is deliberately left out of
auto-start because it needs a light-control method (Shortcuts/Hue/Home
Assistant/Tuya) configured first — see [lights-bridge/README.md](./lights-bridge/).
I didn't want a module that fails on a fresh install.

## 6. Getting it in front of me

A coach you have to remember to open is a coach you stop using. So the last three
modules exist purely to put it where I'll actually see it.

**base-menubar** is a macOS menu bar widget, and the one piece written in Swift
rather than Python. **alerts** sends proactive macOS notifications for recovery,
risky days and bedtime. And **lights-bridge** dims the lights when it's time to
wind down, which is the one that works on me whether I like it or not.

## 7. Running it, and keeping it running

```bash
# 1. Install every module (creates a venv per module, builds base-menubar)
./setup.sh

# 2. Get your own credentials (one-time, per person):
#    - WHOOP developer app → whoop-core/README.md "Setup"
#    - Google Calendar OAuth → calendar-intel/README.md "Setup"

# 3. Authenticate (opens a browser for each)
cd whoop-core     && .venv/bin/whoop-core auth      && cd ..
cd calendar-intel && .venv/bin/calendar-intel auth  && cd ..

# 4. Start everything and make it survive reboot/logout
./scripts/install-launchd.sh
```

That covers whoop-core, calendar-intel, hevy-intel, recovery-forecast, alerts,
and base-menubar.

The bit that made it a real tool rather than a thing I ran manually was step 4 —
it makes everything **survive a reboot or a logout**. Check on things any time
with `launchctl list | grep com.base`; logs land in `~/.base/logs/`.
