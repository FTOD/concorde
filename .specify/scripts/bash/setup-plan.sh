#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            echo "Usage: $0 [--json]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
            exit 0
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
done

# Get script directory and load common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get all paths and variables from common functions
_paths_output=$(get_feature_paths) || { echo "ERROR: Failed to resolve feature paths" >&2; exit 1; }
eval "$_paths_output"
unset _paths_output

if [[ ! -f "$FEATURE_TLDR" || ! -f "$FEATURE_SPEC" || ! -f "$FEATURE_DESIGN" ]]; then
    echo "ERROR: Planning requires the durable tldr.md, spec.md, and design.md trio in $FEATURE_DIR" >&2
    echo "Run \$speckit-specify first to create or migrate the feature root." >&2
    exit 1
fi

# Ensure the durable feature root and temporal implementation workspace exist.
mkdir -p "$FEATURE_DIR" "$IMPLEMENTATION_DIR"

# Copy plan template if plan doesn't already exist
if [[ -f "$IMPL_PLAN" ]]; then
    if $JSON_MODE; then
        echo "Plan already exists at $IMPL_PLAN, skipping template copy" >&2
    else
        echo "Plan already exists at $IMPL_PLAN, skipping template copy"
    fi
else
    if resolve_template_content "plan-template" "$REPO_ROOT" > "$IMPL_PLAN"; then
        if $JSON_MODE; then
            echo "Copied plan template to $IMPL_PLAN" >&2
        else
            echo "Copied plan template to $IMPL_PLAN"
        fi
    else
        resolve_status=$?
        rm -f "$IMPL_PLAN"
        if [ "$resolve_status" -ne 1 ]; then
            exit "$resolve_status"
        fi
        if $JSON_MODE; then
            echo "Warning: Plan template not found" >&2
        else
            echo "Warning: Plan template not found"
        fi
        touch "$IMPL_PLAN"
    fi
fi

# Output results
if $JSON_MODE; then
    if has_jq; then
        jq -cn \
            --arg feature_spec "$FEATURE_SPEC" \
            --arg feature_design "$FEATURE_DESIGN" \
            --arg impl_plan "$IMPL_PLAN" \
            --arg implementation_dir "$IMPLEMENTATION_DIR" \
            --arg specs_dir "$FEATURE_DIR" \
            --arg branch "$CURRENT_BRANCH" \
            '{FEATURE_SPEC:$feature_spec,FEATURE_DESIGN:$feature_design,IMPL_PLAN:$impl_plan,IMPLEMENTATION_DIR:$implementation_dir,SPECS_DIR:$specs_dir,BRANCH:$branch}'
    else
        printf '{"FEATURE_SPEC":"%s","FEATURE_DESIGN":"%s","IMPL_PLAN":"%s","IMPLEMENTATION_DIR":"%s","SPECS_DIR":"%s","BRANCH":"%s"}\n' \
            "$(json_escape "$FEATURE_SPEC")" "$(json_escape "$FEATURE_DESIGN")" "$(json_escape "$IMPL_PLAN")" "$(json_escape "$IMPLEMENTATION_DIR")" "$(json_escape "$FEATURE_DIR")" "$(json_escape "$CURRENT_BRANCH")"
    fi
else
    echo "FEATURE_SPEC: $FEATURE_SPEC"
    echo "FEATURE_DESIGN: $FEATURE_DESIGN"
    echo "IMPL_PLAN: $IMPL_PLAN"
    echo "IMPLEMENTATION_DIR: $IMPLEMENTATION_DIR"
    echo "SPECS_DIR: $FEATURE_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
fi
