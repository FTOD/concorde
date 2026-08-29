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

if [[ ! -f "$FEATURE_ABSTRACT" || ! -f "$FEATURE_DESIGN" || ! -f "$FEATURE_IMPLEMENTATION" ]]; then
    echo "ERROR: Planning requires the durable abstract.md, design.md, and implementation.md trio in $FEATURE_DIR" >&2
    echo "Run \$speckit-specify first to create or migrate the feature root." >&2
    exit 1
fi

# Ensure the durable feature root and temporal implementation workspace exist.
mkdir -p "$FEATURE_DIR" "$ATTEMPT_DIR"

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
            --arg feature_design "$FEATURE_DESIGN" \
            --arg feature_implementation "$FEATURE_IMPLEMENTATION" \
            --arg impl_plan "$IMPL_PLAN" \
            --arg attempt_dir "$ATTEMPT_DIR" \
            --arg specs_dir "$FEATURE_DIR" \
            --arg branch "$CURRENT_BRANCH" \
            '{FEATURE_DESIGN:$feature_design,FEATURE_IMPLEMENTATION:$feature_implementation,IMPL_PLAN:$impl_plan,ATTEMPT_DIR:$attempt_dir,SPECS_DIR:$specs_dir,BRANCH:$branch}'
    else
        printf '{"FEATURE_DESIGN":"%s","FEATURE_IMPLEMENTATION":"%s","IMPL_PLAN":"%s","ATTEMPT_DIR":"%s","SPECS_DIR":"%s","BRANCH":"%s"}\n' \
            "$(json_escape "$FEATURE_DESIGN")" "$(json_escape "$FEATURE_IMPLEMENTATION")" "$(json_escape "$IMPL_PLAN")" "$(json_escape "$ATTEMPT_DIR")" "$(json_escape "$FEATURE_DIR")" "$(json_escape "$CURRENT_BRANCH")"
    fi
else
    echo "FEATURE_DESIGN: $FEATURE_DESIGN"
    echo "FEATURE_IMPLEMENTATION: $FEATURE_IMPLEMENTATION"
    echo "IMPL_PLAN: $IMPL_PLAN"
    echo "ATTEMPT_DIR: $ATTEMPT_DIR"
    echo "SPECS_DIR: $FEATURE_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
fi
