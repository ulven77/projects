# terminfo

**A database that tells terminal emulators and programs how to control the screen.**

Each entry describes a terminal type's capabilities — cursor movement, color support, key sequences, etc. When a new terminal emulator ships (like Ghostty with `xterm-ghostty`), its terminfo entry may not be pre-installed on the system, causing garbled rendering or missing features. The fix is to copy the entry from the app's own files into `/usr/share/terminfo/`. Came up 2026-05-02 when Ghostty's terminfo was missing from the system, silently causing rendering issues.

*First encountered: 2026-05-02*
