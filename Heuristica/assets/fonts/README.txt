This build environment has no internet access, so the JetBrains Mono and
IBM Plex Sans .ttf files could not be downloaded into this folder.

The app runs fine without them: fonts.py checks for these exact filenames
here, and falls back to a system monospace/sans-serif font if they're
missing, so nothing crashes -- the look will just use your OS's default
fonts instead of the intended typefaces.

To get the intended look, download these (both are free/open-source) and
drop them in this folder with these exact names:

  JetBrainsMono-Regular.ttf   https://www.jetbrains.com/lp/mono/
  JetBrainsMono-Bold.ttf
  IBMPlexSans-Regular.ttf     https://fonts.google.com/specimen/IBM+Plex+Sans
  IBMPlexSans-Bold.ttf
