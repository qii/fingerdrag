# Immediate drag in this fork

The configured drag finger count is reserved for dragging. On libinput
1.31/1.32, the extra `0003` patch skips the 80 ms fast-swipe decision window,
uses the existing drag-start handler to press the left button, and forwards
any queued motion in the same input frame. It does not emit a tentative
swipe. It also removes the now-unused timer-setting helper.

This removes this particular software delay, not all hardware or
finger-count detection latency. Swipes with the configured drag finger
count are lost. Other finger counts and the existing release/reposition
logic are unchanged. The upstream tap-to-click patch still means that
three-finger drag takes over the three-finger tap.

## Install or replace an existing upstream fingerdrag installation

```sh
git clone https://github.com/qii/fingerdrag.git fingerdrag-instant
cd fingerdrag-instant
./fingerdrag doctor
./fingerdrag install --fingers 3
```

Run the checkout's `./fingerdrag`, not an older installed `fingerdrag`.
The installer rebuilds from distribution sources, increments the local
package revision, and copies this fork's patch series to the installed
tool. No prior uninstall is needed. Log out and back in after installation.
The build summary should list three patches for series 1.31 or 1.32.

Future `fingerdrag install` runs use the copied patches. Reinstalling the
original upstream tool would replace them. A future libinput source change
may require refreshing the patches; do not force a failing patch to apply.

Restore distribution packages with `fingerdrag uninstall`, then log out
and back in.

## Validation (2026-10-10)

- All three patches apply to the upstream 1.31.1 and 1.32.0 gesture/tap
  sources. Separate series are needed because 1.32 changed the timer helper.
- `tests/instant-drag.py` extracts the actual drag-start, drag-motion and
  swipe-or-drag entry handlers from patched C source, compiles them with
  mocked event sinks, and verifies button-before-motion ordering without a
  swipe or timer, no duplicate button on continued motion, and no invented
  motion when stationary. Both configured finger counts (3 and 4) pass.
- The same test fails on the unmodified 1.31.1 entry handler: it emits a
  swipe and arms a timer instead of pressing and moving. This checks that
  the regression test detects the original delay.
- Shell syntax checks and `git diff --check` pass.

These are patch-application and isolated-handler checks. They do not cover
the full libinput state machine, Ubuntu package compilation or physical
touchpad behavior. The local development host is macOS without Docker, so
the upstream container build/install/uninstall suite has not been run
locally. The existing end-to-end CI jobs are retained; the new
`instant-drag` CI job checks both source versions and event ordering.

To run the handler check against an already-patched source tree:

```sh
python3 tests/instant-drag.py /path/to/libinput/src/evdev-mt-touchpad-gestures.c
```

The first target system is Kubuntu 26.04.1, Wayland/KDE, with distribution
libinput `1.31.1-1ubuntu1.2`. Physical testing of this fork is still pending.
