#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_PATH="${1:-$(cd "$SCRIPT_DIR/../../../.." && pwd)}"
CRM_PATH="$BENCH_PATH/apps/crm"
PATCH_FILE="$SCRIPT_DIR/patches/crm-sms-tab.patch"
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

echo "Checking that the patch applies cleanly..."
if ! git -C "$CRM_PATH" apply --check "$PATCH_FILE" 2>/tmp/crm-sms-tab-patch-check.log; then
	echo "" >&2
	echo "error: crm-sms-tab.patch does not apply cleanly against this apps/crm checkout." >&2
	echo "CRM's frontend has likely changed upstream since this patch was captured." >&2
	echo "Manual re-diffing of the patch against the current crm frontend is required." >&2
	echo "" >&2
	echo "git apply output:" >&2
	cat /tmp/crm-sms-tab-patch-check.log >&2
	exit 1
fi

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
