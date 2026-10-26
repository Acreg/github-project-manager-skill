#!/bin/sh
set -eu
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
src="$repo_dir/skills/github-project-manager"
[ -f "$src/SKILL.md" ] || { echo "Missing skills/github-project-manager/SKILL.md" >&2; exit 1; }
timestamp=$(date '+%Y%m%d-%H%M%S')
for destroot in "$HOME/.agents/skills" "$HOME/.dsh/skills"; do
    mkdir -p "$destroot"
    dest="$destroot/github-project-manager"
    if [ -e "$dest" ]; then
        archive="$HOME/.agent-skills-backups/$timestamp"
        mkdir -p "$archive"
        mv "$dest" "$archive/$(basename "$destroot")-github-project-manager-$$"
        echo "Previous skill backed up under $archive"
    fi
    cp -R "$src" "$dest"
    [ -f "$dest/SKILL.md" ] || { echo "Skill install failed: $dest" >&2; exit 1; }
    echo "Installed: $dest"
done
echo "GitHub authentication is not modified."
