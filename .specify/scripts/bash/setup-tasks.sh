#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false

for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h)
            echo "Usage: $0 [--json]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
            exit 0
            ;;
        *) echo "ERROR: Unknown option '$arg'" >&2; exit 1 ;;
    esac
done

# Source common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get feature paths
_paths_output=$(get_feature_paths) || { echo "ERROR: Failed to resolve feature paths" >&2; exit 1; }
eval "$_paths_output"
unset _paths_output

# Validate required files
if [[ ! -f "$IMPL_PLAN" ]]; then
    echo "ERROR: plan.md not found in $ATTEMPT_DIR" >&2
    echo "Run \$speckit-plan first to create the implementation plan." >&2
    exit 1
fi

if [[ ! -f "$FEATURE_DESIGN" ]]; then
    echo "ERROR: design.md not found in $FEATURE_DIR" >&2
    echo "Run \$speckit-specify first to create the feature structure." >&2
    exit 1
fi

if [[ ! -f "$FEATURE_IMPLEMENTATION" ]]; then
    echo "ERROR: implementation.md not found in $FEATURE_DIR" >&2
    echo "Run \$speckit-specify first to create the accepted realization baseline." >&2
    exit 1
fi

# Build available docs list
docs=()
[[ -f "$FEATURE_ABSTRACT" ]] && docs+=("abstract.md")
docs+=("implementation.md")
[[ -f "$RESEARCH" ]] && docs+=("attempt/research.md")
[[ -f "$DATA_MODEL" ]] && docs+=("attempt/data-model.md")
if [[ -d "$CONTRACTS_DIR" ]] && [[ -n "$(ls -A "$CONTRACTS_DIR" 2>/dev/null)" ]]; then
    docs+=("contracts/")
fi
[[ -f "$QUICKSTART" ]] && docs+=("attempt/quickstart.md")

# Resolve tasks template through override stack
TASKS_TEMPLATE=$(resolve_template "tasks-template" "$REPO_ROOT") || true
if TASKS_TEMPLATE_CONTENT=$(resolve_template_content "tasks-template" "$REPO_ROOT"; status=$?; printf x; exit "$status"); then
    TASKS_TEMPLATE_CONTENT="${TASKS_TEMPLATE_CONTENT%x}"
else
    echo "ERROR: Could not resolve required tasks-template from the template override stack for $REPO_ROOT" >&2
    echo "Template 'tasks-template' was not found in any supported location (overrides, presets, extensions, or shared core). Add an override at .specify/templates/overrides/tasks-template.md, or run 'specify init' / reinstall shared infra to restore the core .specify/templates/tasks-template.md template." >&2
    exit 1
fi

# Output results
if $JSON_MODE; then
    if has_jq; then
        if [[ ${#docs[@]} -eq 0 ]]; then
            json_docs="[]"
        else
            json_docs=$(printf '%s\n' "${docs[@]}" | jq -R . | jq -s .)
        fi
        jq -cn \
            --arg feature_dir "$FEATURE_DIR" \
            --arg attempt_dir "$ATTEMPT_DIR" \
            --arg feature_design "$FEATURE_DESIGN" \
            --arg feature_implementation "$FEATURE_IMPLEMENTATION" \
            --arg impl_plan "$IMPL_PLAN" \
            --arg tasks "$TASKS" \
            --argjson docs "$json_docs" \
            --arg tasks_template "${TASKS_TEMPLATE:-}" \
            --arg tasks_template_content "$TASKS_TEMPLATE_CONTENT" \
            '{FEATURE_DIR:$feature_dir,ATTEMPT_DIR:$attempt_dir,FEATURE_DESIGN:$feature_design,FEATURE_IMPLEMENTATION:$feature_implementation,IMPL_PLAN:$impl_plan,TASKS:$tasks,AVAILABLE_DOCS:$docs,TASKS_TEMPLATE:$tasks_template,TASKS_TEMPLATE_CONTENT:$tasks_template_content}'
    else
        if [[ ${#docs[@]} -eq 0 ]]; then
            json_docs="[]"
        else
            json_docs=$(for d in "${docs[@]}"; do printf '"%s",' "$(json_escape "$d")"; done)
            json_docs="[${json_docs%,}]"
        fi
        printf '{"FEATURE_DIR":"%s","ATTEMPT_DIR":"%s","FEATURE_DESIGN":"%s","FEATURE_IMPLEMENTATION":"%s","IMPL_PLAN":"%s","TASKS":"%s","AVAILABLE_DOCS":%s,"TASKS_TEMPLATE":"%s","TASKS_TEMPLATE_CONTENT":"%s"}\n' \
            "$(json_escape "$FEATURE_DIR")" "$(json_escape "$ATTEMPT_DIR")" "$(json_escape "$FEATURE_DESIGN")" "$(json_escape "$FEATURE_IMPLEMENTATION")" "$(json_escape "$IMPL_PLAN")" "$(json_escape "$TASKS")" "$json_docs" "$(json_escape "${TASKS_TEMPLATE:-}")" "$(json_escape "$TASKS_TEMPLATE_CONTENT")"
    fi
else
    echo "FEATURE_DIR: $FEATURE_DIR"
    echo "ATTEMPT_DIR: $ATTEMPT_DIR"
    echo "FEATURE_DESIGN: $FEATURE_DESIGN"
    echo "FEATURE_IMPLEMENTATION: $FEATURE_IMPLEMENTATION"
    echo "IMPL_PLAN: $IMPL_PLAN"
    echo "TASKS: $TASKS"
    echo "TASKS_TEMPLATE: ${TASKS_TEMPLATE:-not found}"
    echo "AVAILABLE_DOCS:"
    check_file "$RESEARCH" "attempt/research.md"
    check_file "$DATA_MODEL" "attempt/data-model.md"
    check_dir "$CONTRACTS_DIR" "contracts/"
    check_file "$QUICKSTART" "attempt/quickstart.md"
fi
