# Patch series

Each directory holds the series for a range of libinput releases. The name is
the first release the series applies to; `fingerdrag` picks the highest
directory that is not newer than the libinput being built.

| Directory | Applies to | Patches | Tested on hardware |
|-----------|------------|---------|--------------------|
| `1.28`    | 1.28 to 1.30 | default-on only | no, apply-tested only |
| `1.31`    | 1.31 | default-on, finger-down entry with tap-to-click, immediate drag | extra patch not yet hardware-tested |
| `1.32`    | 1.32 and later compatible versions | same behavior, adapted to the changed timer helper | not yet hardware-tested |

This fork adds `0003-instant-finger-drag.patch` in both the `1.31` and
`1.32` series. It bypasses the
swipe-or-drag start state, calls the existing drag-start handler, and then
forwards motion queued in that frame. The now-unused timer-setting helper
is removed too, avoiding an unused-static-function warning. The configured
finger count no longer produces swipe events. Release/reposition timing is
unchanged. See [fork validation](../docs/INSTANT-DRAG.md).

Releases before 1.31 have no fast-swipe disambiguation, so the drag does not
need the finger-down entry fix there.

The first patch carries one line, `#define FINGERDRAG_DEFAULT_NFINGERS 3`,
that `fingerdrag` rewrites at build time for `--fingers`. The value is also
embedded as the string `FINGERDRAG_BUILTIN_NFINGERS=<n>` so that the default
of an installed library can be read back. Keep both when refreshing.

Backports use the series that matches the newer source, so Ubuntu 24.04 gets
the `1.31` series and Debian 12 gets the `1.28` series.

The patches are `git format-patch` output against upstream libinput tags and
are applied with `patch -p1`. To refresh them, rebase the two commits onto the
new tag and re-export.

To get the series back as a branch: `git checkout -b fingerdrag-1.31 1.31.1`
in a libinput clone (`~/projects/libinput` has one), then
`git am patches/1.31/*.patch`.
