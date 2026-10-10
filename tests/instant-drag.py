#!/usr/bin/env python3
"""Check event ordering in actual patched C handlers, using mocked sinks.

Usage: python3 tests/instant-drag.py /path/to/patched/libinput/src/evdev-mt-touchpad-gestures.c
This is an isolated handler test, not a full libinput or hardware test.
"""

import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile


def function(source, name):
    start = source.index("static void\n" + name + "(")
    brace = source.index("{", start)
    depth = 0
    for end in range(brace, len(source)):
        depth += (source[end] == "{") - (source[end] == "}")
        if depth == 0:
            return source[start : end + 1]
    raise ValueError("Unclosed function: " + name)


source = Path(sys.argv[1]).read_text()
handlers = "\n\n".join(
    function(source, name)
    for name in (
        "tp_gesture_handle_state_3fg_drag_start",
        "tp_gesture_handle_state_3fg_drag",
        "tp_gesture_handle_state_3fg_drag_or_swipe_start",
    )
)

fixture = r"""
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
typedef unsigned long long usec_t;
enum {
    EVDEV_BTN_LEFT = 272, LIBINPUT_BUTTON_STATE_PRESSED = 1,
    TOUCHPAD_EVENT_MOTION = 2, GESTURE_STATE_3FG_DRAG = 3,
    GESTURE_STATE_3FG_DRAG_OR_SWIPE = 4,
    LIBINPUT_EVENT_GESTURE_SWIPE_BEGIN = 5
};
struct normalized_coords { double x, y; };
struct mock_device { int base; };
struct tp_dispatch {
    struct mock_device *device;
    int queued;
    struct { int state, finger_count; } gesture;
};
static char events[16];
static unsigned count;
static usec_t now = 123456;
static void require(int ok, const char *message) {
    if (!ok) { fprintf(stderr, "%s (events=%s)\n", message, events); exit(1); }
}
static void event(char kind, usec_t time) {
    require(time == now, "event timestamp changed");
    require(count + 1 < sizeof(events), "too many events");
    events[count++] = kind;
    events[count] = '\0';
}
static int evdev_usage_from(int button) { return button; }
static void evdev_pointer_notify_button(void *device, usec_t time, int button, int state) {
    require(button == EVDEV_BTN_LEFT, "wrong button");
    require(state == LIBINPUT_BUTTON_STATE_PRESSED, "not a button press");
    event('B', time);
}
static void tp_gesture_post_pointer_motion(struct tp_dispatch *tp, usec_t time) {
    event('M', time);
}
/* These stubs also allow testing the upstream two-patch baseline. */
static void gesture_notify_swipe(void *device, usec_t time, int type, int fingers,
    const struct normalized_coords *delta, const struct normalized_coords *raw) {
    event('S', time);
}
static void tp_gesture_set_3fg_drag_3fg_or_swipe_timer(struct tp_dispatch *tp, usec_t time) {
    event('T', time);
}
"""

checks = r"""
int main(void) {
    for (int fingers = 3; fingers <= 4; fingers++) {
        struct mock_device device = {0};
        struct tp_dispatch tp = {0};
        tp.device = &device;
        tp.gesture.finger_count = fingers;
        tp.queued = TOUCHPAD_EVENT_MOTION;
        count = 0; events[0] = '\0';
        tp_gesture_handle_state_3fg_drag_or_swipe_start(&tp, now);
        require(strcmp(events, "BM") == 0,
            "first moving frame must press then move, without swipe/timer");
        require(tp.gesture.state == GESTURE_STATE_3FG_DRAG, "drag not active");
        count = 0; events[0] = '\0';
        tp_gesture_handle_state_3fg_drag(&tp, now);
        require(strcmp(events, "M") == 0, "continuing motion must not press again");

        tp.queued = 0;
        count = 0; events[0] = '\0';
        tp_gesture_handle_state_3fg_drag_or_swipe_start(&tp, now);
        require(strcmp(events, "B") == 0, "stationary start must not invent motion");
        count = 0; events[0] = '\0';
        tp_gesture_handle_state_3fg_drag(&tp, now);
        require(count == 0, "stationary continuation emitted an event");
    }
    puts("PASS: immediate button/motion ordering for configured 3/4-finger drag");
    return 0;
}
"""

with tempfile.TemporaryDirectory(prefix="fingerdrag-test-") as directory:
    directory = Path(directory)
    test = directory / "handlers.c"
    executable = directory / "handlers"
    test.write_text(fixture + handlers + checks)
    subprocess.run(
        shlex.split(os.environ.get("CC", "cc"))
        + ["-std=c99", "-Wall", "-Wextra", "-Werror",
           "-Wno-unused-function", "-Wno-unused-parameter",
           str(test), "-o", str(executable)],
        check=True,
    )
    subprocess.run([str(executable)], check=True)
