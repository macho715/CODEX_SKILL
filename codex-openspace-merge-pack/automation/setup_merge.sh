#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: bash automation/setup_merge.sh /abs/path/to/OpenSpace /abs/path/to/repo"
  exit 1
fi

OPENSPACE_DIR="$1"
REPO_DIR="$2"

mkdir -p "$REPO_DIR/.agents/skills"
mkdir -p "$REPO_DIR/.codex"

cp -R "$OPENSPACE_DIR/openspace/host_skills/delegate-task" "$REPO_DIR/.agents/skills/"
cp -R "$OPENSPACE_DIR/openspace/host_skills/skill-discovery" "$REPO_DIR/.agents/skills/"
cp -R "$(cd "$(dirname "$0")/.." && pwd)/.agents/skills/openspace-bridge" "$REPO_DIR/.agents/skills/"

sed \
  -e "s|/ABS/PATH/TO/REPO/.agents/skills|$REPO_DIR/.agents/skills|g" \
  -e "s|/ABS/PATH/TO/OpenSpace|$OPENSPACE_DIR|g" \
  "$(cd "$(dirname "$0")/.." && pwd)/.codex/config.toml.example" \
  > "$REPO_DIR/.codex/config.toml"

echo "Merge setup complete."
echo "1) Confirm Codex MCP config at: $REPO_DIR/.codex/config.toml"
echo "2) Append AGENTS.merge-snippet.md into your repo AGENTS.md"
echo "3) Run the launcher or Streamlit app from the repo root"
