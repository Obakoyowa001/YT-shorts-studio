#!/usr/bin/env bash
# Downloads open-licensed assets that aren't stored in the repo.
#   fonts : Rye (OFL) + Luckiest Guy (Apache 2.0) from Google Fonts
#   voices: Piper offline backup voice (en_US-ryan-high) from rhasspy/piper-voices
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
what="${1:-all}"
if [[ "$what" == fonts || "$what" == all ]]; then
  mkdir -p "$here/fonts"
  curl -fsSL -o "$here/fonts/Rye-Regular.ttf" https://github.com/google/fonts/raw/main/ofl/rye/Rye-Regular.ttf
  curl -fsSL -o "$here/fonts/LuckiestGuy-Regular.ttf" https://github.com/google/fonts/raw/main/apache/luckiestguy/LuckiestGuy-Regular.ttf
fi
if [[ "$what" == voices || "$what" == all ]]; then
  mkdir -p "$here/voices"
  base=https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high
  curl -fsSL -o "$here/voices/en_US-ryan-high.onnx" "$base/en_US-ryan-high.onnx"
  curl -fsSL -o "$here/voices/en_US-ryan-high.onnx.json" "$base/en_US-ryan-high.onnx.json"
fi
