#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_PATH="${1:-$(cd "$SCRIPT_DIR/../../../.." && pwd)}"
CRM_PATH="$BENCH_PATH/apps/crm"
PATCHES_DIR="$SCRIPT_DIR/patches"
OVERLAY_DIR="$SCRIPT_DIR/overlay/src"

if [ ! -d "$CRM_PATH/frontend/src" ]; then
	echo "error: could not find $CRM_PATH/frontend/src -- pass the bench path explicitly:" >&2
	echo "  bash apply_sms_tab.sh /path/to/bench" >&2
	exit 1
fi

if ! git -C "$CRM_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
	echo "error: $CRM_PATH is not a git checkout -- cannot safely apply/verify the patch" >&2
	exit 1
fi

if ! git -C "$CRM_PATH" diff --quiet -- frontend/src; then
	echo "error: apps/crm/frontend/src has uncommitted changes already." >&2
	echo "This script only applies cleanly against a pristine crm frontend checkout." >&2
	echo "Commit/stash/revert your changes first, then re-run." >&2
	exit 1
fi

CRM_BRANCH="$(git -C "$CRM_PATH" branch --show-current 2>/dev/null || true)"

PATCH_FILE=""
if [ -n "$CRM_BRANCH" ] && [ -f "$PATCHES_DIR/crm-sms-tab-$CRM_BRANCH.patch" ]; then
	if git -C "$CRM_PATH" apply --check "$PATCHES_DIR/crm-sms-tab-$CRM_BRANCH.patch" 2>/dev/null; then
		PATCH_FILE="$PATCHES_DIR/crm-sms-tab-$CRM_BRANCH.patch"
	fi
fi

if [ -z "$PATCH_FILE" ]; then
	for candidate in "$PATCHES_DIR"/crm-sms-tab-*.patch; do
		[ -f "$candidate" ] || continue
		if git -C "$CRM_PATH" apply --check "$candidate" 2>/dev/null; then
			PATCH_FILE="$candidate"
			break
		fi
	done
fi

if [ -z "$PATCH_FILE" ]; then
	echo "" >&2
	echo "error: no bundled patch applies cleanly against this apps/crm checkout (branch: ${CRM_BRANCH:-detached})." >&2
	echo "CRM's frontend has diverged from every version this app has a patch for." >&2
	echo "Manual re-diffing of a patch against the current crm frontend is required." >&2
	exit 1
fi

echo "Using $(basename "$PATCH_FILE")"
echo "Applying patch..."
git -C "$CRM_PATH" apply "$PATCH_FILE"

echo "Copying overlay files (new SMS components)..."
cp -r "$OVERLAY_DIR/." "$CRM_PATH/frontend/src/"

if ! command -v yarn >/dev/null 2>&1; then
	echo "error: yarn not found on PATH -- install it, then run 'yarn install && yarn build' inside $CRM_PATH/frontend manually" >&2
	exit 1
fi

echo "Installing frontend dependencies and building CRM..."
(cd "$CRM_PATH/frontend" && NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=4096}" yarn install && NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=4096}" yarn build)

echo ""
echo "Done. The SMS tab is now built into crm's frontend bundle."
echo "If bench is already running, restart it (bench restart, or your process manager's"
echo "equivalent) and hard-refresh the browser to pick up the new assets."
