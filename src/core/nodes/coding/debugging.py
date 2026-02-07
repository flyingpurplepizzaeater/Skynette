"""
Error Handling and Debugging Nodes - Continuous loops for error detection, fixing, and verification.

These nodes enable automated debugging workflows:
1. Detect errors in code/tests
2. Attempt fixes (via AI or predefined strategies)
3. Verify fixes work
4. Loop until resolved or max attempts reached
"""

import asyncio

from src.core.nodes.base import BaseNode, FieldType, NodeField


class TryCatchNode(BaseNode):
    """
    Try-Catch wrapper node for error handling.
    Executes input and catches any errors, allowing workflow to continue.
    """

    type = "try-catch"
    name = "Flow: Try-Catch"
    category = "Coding"
    description = "Wrap execution in try-catch for error handling"
    icon = "shield"
    color = "#DC3545"  # Red for error handling

    inputs = [
        NodeField(
            name="input_data",
            label="Input Data",
            type=FieldType.JSON,
            required=False,
            description="Data to pass through (from previous node).",
        ),
        NodeField(
            name="error_input",
            label="Error Input",
            type=FieldType.STRING,
            required=False,
            description="Error from previous node (if any).",
        ),
        NodeField(
            name="success_input",
            label="Success Input",
            type=FieldType.BOOLEAN,
            required=False,
            default=True,
            description="Success status from previous node.",
        ),
    ]

    outputs = [
        NodeField(name="data", label="Output Data", type=FieldType.JSON),
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="has_error", label="Has Error", type=FieldType.BOOLEAN),
        NodeField(name="error_message", label="Error Message", type=FieldType.STRING),
        NodeField(name="should_retry", label="Should Retry", type=FieldType.BOOLEAN),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        input_data = config.get("input_data", {})
        error_input = config.get("error_input", "")
        success_input = config.get("success_input", True)

        has_error = bool(error_input) or not success_input

        return {
            "data": input_data,
            "success": not has_error,
            "has_error": has_error,
            "error_message": error_input if has_error else "",
            "should_retry": has_error,  # Signal for retry loop
        }


class RetryLoopNode(BaseNode):
    """
    Retry loop node - retries failed operations with configurable strategies.
    """

    type = "retry-loop"
    name = "Flow: Retry Loop"
    category = "Coding"
    description = "Retry failed operations with exponential backoff"
    icon = "refresh"
    color = "#FFC107"  # Warning yellow

    inputs = [
        NodeField(
            name="success",
            label="Operation Success",
            type=FieldType.BOOLEAN,
            required=True,
            description="Whether the previous operation succeeded.",
        ),
        NodeField(
            name="attempt",
            label="Current Attempt",
            type=FieldType.NUMBER,
            required=False,
            default=1,
        ),
        NodeField(
            name="max_attempts",
            label="Max Attempts",
            type=FieldType.NUMBER,
            required=False,
            default=3,
        ),
        NodeField(
            name="delay_seconds",
            label="Base Delay (seconds)",
            type=FieldType.NUMBER,
            required=False,
            default=1,
        ),
        NodeField(
            name="exponential_backoff",
            label="Exponential Backoff",
            type=FieldType.BOOLEAN,
            required=False,
            default=True,
        ),
    ]

    outputs = [
        NodeField(name="should_retry", label="Should Retry", type=FieldType.BOOLEAN),
        NodeField(name="next_attempt", label="Next Attempt Number", type=FieldType.NUMBER),
        NodeField(name="wait_seconds", label="Wait Before Retry", type=FieldType.NUMBER),
        NodeField(name="final_failure", label="Final Failure", type=FieldType.BOOLEAN),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        success = config.get("success", False)
        attempt = int(config.get("attempt", 1))
        max_attempts = int(config.get("max_attempts", 3))
        delay_seconds = float(config.get("delay_seconds", 1))
        exponential_backoff = config.get("exponential_backoff", True)

        if success:
            return {
                "should_retry": False,
                "next_attempt": attempt,
                "wait_seconds": 0,
                "final_failure": False,
            }

        if attempt >= max_attempts:
            return {
                "should_retry": False,
                "next_attempt": attempt,
                "wait_seconds": 0,
                "final_failure": True,
            }

        # Calculate wait time
        if exponential_backoff:
            wait = delay_seconds * (2 ** (attempt - 1))
        else:
            wait = delay_seconds

        return {
            "should_retry": True,
            "next_attempt": attempt + 1,
            "wait_seconds": wait,
            "final_failure": False,
        }


class ErrorDetectorNode(BaseNode):
    """
    Analyze output for errors and classify them.
    """

    type = "error-detector"
    name = "Debug: Error Detector"
    category = "Coding"
    description = "Detect and classify errors from execution output"
    icon = "bug_report"
    color = "#DC3545"

    inputs = [
        NodeField(name="stdout", label="Standard Output", type=FieldType.TEXT, required=False),
        NodeField(name="stderr", label="Standard Error", type=FieldType.TEXT, required=False),
        NodeField(
            name="return_code",
            label="Return Code",
            type=FieldType.NUMBER,
            required=False,
            default=0,
        ),
        NodeField(name="test_output", label="Test Output", type=FieldType.TEXT, required=False),
    ]

    outputs = [
        NodeField(name="has_errors", label="Has Errors", type=FieldType.BOOLEAN),
        NodeField(name="error_count", label="Error Count", type=FieldType.NUMBER),
        NodeField(name="errors", label="Detected Errors", type=FieldType.JSON),
        NodeField(name="error_types", label="Error Types", type=FieldType.JSON),
        NodeField(name="severity", label="Severity", type=FieldType.STRING),
        NodeField(name="suggested_fixes", label="Suggested Fix Categories", type=FieldType.JSON),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        stdout = config.get("stdout", "")
        stderr = config.get("stderr", "")
        return_code = int(config.get("return_code", 0))
        test_output = config.get("test_output", "")

        combined = f"{stdout}\n{stderr}\n{test_output}"
        errors = []
        error_types = set()
        suggested_fixes = []

        import re

        # Python errors
        python_errors = {
            r"SyntaxError": ("SyntaxError", "syntax", "Check syntax near the indicated line"),
            r"IndentationError": ("IndentationError", "syntax", "Fix indentation"),
            r"NameError": ("NameError", "reference", "Check variable/function names"),
            r"TypeError": ("TypeError", "type", "Check argument types"),
            r"ValueError": ("ValueError", "value", "Check input values"),
            r"ImportError": ("ImportError", "import", "Check module installation"),
            r"ModuleNotFoundError": ("ModuleNotFoundError", "import", "Install missing module"),
            r"AttributeError": ("AttributeError", "attribute", "Check object attributes"),
            r"KeyError": ("KeyError", "key", "Check dictionary keys"),
            r"IndexError": ("IndexError", "index", "Check list/array bounds"),
            r"FileNotFoundError": ("FileNotFoundError", "file", "Check file paths"),
            r"PermissionError": ("PermissionError", "permission", "Check file permissions"),
            r"ConnectionError": ("ConnectionError", "network", "Check network connection"),
            r"TimeoutError": ("TimeoutError", "timeout", "Increase timeout or optimize"),
        }

        # JavaScript errors
        js_errors = {
            r"ReferenceError": ("ReferenceError", "reference", "Check variable declarations"),
            r"SyntaxError": ("SyntaxError", "syntax", "Fix JavaScript syntax"),
            r"TypeError": ("TypeError", "type", "Check types and null values"),
            r"RangeError": ("RangeError", "range", "Check numeric ranges"),
        }

        # General patterns
        general_patterns = {
            r"error:": ("GeneralError", "general", "Review error message"),
            r"Error:": ("GeneralError", "general", "Review error message"),
            r"FAILED": ("TestFailure", "test", "Fix failing test"),
            r"failed": ("TestFailure", "test", "Fix failing test"),
            r"Exception": ("Exception", "exception", "Handle exception"),
            r"Traceback": ("Traceback", "runtime", "Review stack trace"),
            r"AssertionError": ("AssertionError", "assertion", "Fix assertion"),
        }

        all_patterns = {**python_errors, **js_errors, **general_patterns}

        for pattern, (error_name, error_type, fix_hint) in all_patterns.items():
            matches = re.findall(f"{pattern}.*", combined, re.IGNORECASE)
            for match in matches:
                errors.append(
                    {
                        "type": error_name,
                        "message": match[:200],
                        "category": error_type,
                    }
                )
                error_types.add(error_type)
                if fix_hint not in suggested_fixes:
                    suggested_fixes.append(fix_hint)

        # Extract line numbers
        line_matches = re.findall(r"[Ll]ine (\d+)", combined)
        file_matches = re.findall(r'[Ff]ile ["\']([^"\']+)["\']', combined)

        for i, error in enumerate(errors):
            if i < len(line_matches):
                errors[i]["line"] = int(line_matches[i])
            if i < len(file_matches):
                errors[i]["file"] = file_matches[i]

        # Determine severity
        if not errors and return_code == 0:
            severity = "none"
        elif len(errors) == 1:
            severity = "low"
        elif len(errors) <= 5:
            severity = "medium"
        else:
            severity = "high"

        # Check for critical errors
        critical_types = {"SyntaxError", "ImportError", "ModuleNotFoundError"}
        if error_types & critical_types:
            severity = "critical"

        return {
            "has_errors": len(errors) > 0 or return_code != 0,
            "error_count": len(errors),
            "errors": errors[:20],  # Limit to 20
            "error_types": list(error_types),
            "severity": severity,
            "suggested_fixes": suggested_fixes,
        }


class DebugLoopNode(BaseNode):
    """
    Main debugging loop node - orchestrates the find-fix-verify cycle.
    This is the core node for automated error fixing workflows.
    """

    type = "debug-loop"
    name = "Debug: Fix Loop"
    category = "Coding"
    description = "Continuous loop: detect errors, fix, verify until resolved"
    icon = "loop"
    color = "#6F42C1"  # Purple for automation

    inputs = [
        NodeField(
            name="has_errors",
            label="Has Errors",
            type=FieldType.BOOLEAN,
            required=True,
            description="Whether errors were detected.",
        ),
        NodeField(
            name="errors",
            label="Error Details",
            type=FieldType.JSON,
            required=False,
            description="List of detected errors.",
        ),
        NodeField(
            name="fix_applied",
            label="Fix Applied",
            type=FieldType.BOOLEAN,
            required=False,
            default=False,
            description="Whether a fix was attempted.",
        ),
        NodeField(
            name="fix_result",
            label="Fix Result",
            type=FieldType.TEXT,
            required=False,
            description="Result of the fix attempt.",
        ),
        NodeField(
            name="iteration",
            label="Current Iteration",
            type=FieldType.NUMBER,
            required=False,
            default=0,
        ),
        NodeField(
            name="max_iterations",
            label="Max Iterations",
            type=FieldType.NUMBER,
            required=False,
            default=5,
        ),
        NodeField(
            name="previous_errors",
            label="Previous Errors",
            type=FieldType.JSON,
            required=False,
            description="Errors from previous iteration (to detect loops).",
        ),
    ]

    outputs = [
        NodeField(name="action", label="Next Action", type=FieldType.STRING),
        NodeField(name="continue_loop", label="Continue Loop", type=FieldType.BOOLEAN),
        NodeField(name="next_iteration", label="Next Iteration", type=FieldType.NUMBER),
        NodeField(name="status", label="Status", type=FieldType.STRING),
        NodeField(name="errors_to_fix", label="Errors to Fix", type=FieldType.JSON),
        NodeField(name="is_resolved", label="Is Resolved", type=FieldType.BOOLEAN),
        NodeField(name="stuck_in_loop", label="Stuck in Loop", type=FieldType.BOOLEAN),
        NodeField(name="summary", label="Summary", type=FieldType.TEXT),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        has_errors = config.get("has_errors", False)
        errors = config.get("errors", [])
        fix_applied = config.get("fix_applied", False)
        fix_result = config.get("fix_result", "")
        iteration = int(config.get("iteration", 0))
        max_iterations = int(config.get("max_iterations", 5))
        previous_errors = config.get("previous_errors", [])

        # Check if we're stuck in a loop (same errors repeating)
        stuck_in_loop = False
        if previous_errors and errors:
            prev_types = {e.get("type") for e in previous_errors if isinstance(e, dict)}
            curr_types = {e.get("type") for e in errors if isinstance(e, dict)}
            if prev_types == curr_types and iteration > 2:
                stuck_in_loop = True

        # Determine next action
        if not has_errors:
            return {
                "action": "complete",
                "continue_loop": False,
                "next_iteration": iteration,
                "status": "RESOLVED",
                "errors_to_fix": [],
                "is_resolved": True,
                "stuck_in_loop": False,
                "summary": f"All errors resolved after {iteration} iterations.",
            }

        if iteration >= max_iterations:
            return {
                "action": "abort",
                "continue_loop": False,
                "next_iteration": iteration,
                "status": "MAX_ITERATIONS_REACHED",
                "errors_to_fix": errors,
                "is_resolved": False,
                "stuck_in_loop": stuck_in_loop,
                "summary": f"Max iterations ({max_iterations}) reached. {len(errors)} errors remain.",
            }

        if stuck_in_loop:
            return {
                "action": "escalate",
                "continue_loop": False,
                "next_iteration": iteration,
                "status": "STUCK_IN_LOOP",
                "errors_to_fix": errors,
                "is_resolved": False,
                "stuck_in_loop": True,
                "summary": "Same errors repeating. Manual intervention needed.",
            }

        # Continue fixing
        return {
            "action": "fix",
            "continue_loop": True,
            "next_iteration": iteration + 1,
            "status": "FIXING",
            "errors_to_fix": errors,
            "is_resolved": False,
            "stuck_in_loop": False,
            "summary": f"Iteration {iteration + 1}: Attempting to fix {len(errors)} error(s).",
        }


class VerifyFixNode(BaseNode):
    """
    Verify that a fix was successful by comparing before/after states.
    """

    type = "verify-fix"
    name = "Debug: Verify Fix"
    category = "Coding"
    description = "Verify a fix resolved the error"
    icon = "verified"
    color = "#28A745"  # Green for success

    inputs = [
        NodeField(
            name="original_error", label="Original Error", type=FieldType.TEXT, required=True
        ),
        NodeField(name="new_output", label="New Output", type=FieldType.TEXT, required=True),
        NodeField(name="new_stderr", label="New Stderr", type=FieldType.TEXT, required=False),
        NodeField(
            name="expected_behavior", label="Expected Behavior", type=FieldType.TEXT, required=False
        ),
        NodeField(name="test_passed", label="Test Passed", type=FieldType.BOOLEAN, required=False),
    ]

    outputs = [
        NodeField(name="fix_verified", label="Fix Verified", type=FieldType.BOOLEAN),
        NodeField(name="original_fixed", label="Original Error Fixed", type=FieldType.BOOLEAN),
        NodeField(name="new_errors", label="New Errors Introduced", type=FieldType.BOOLEAN),
        NodeField(name="confidence", label="Confidence", type=FieldType.NUMBER),
        NodeField(name="verification_details", label="Details", type=FieldType.TEXT),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        original_error = config.get("original_error", "")
        new_output = config.get("new_output", "")
        new_stderr = config.get("new_stderr", "")
        expected_behavior = config.get("expected_behavior", "")
        test_passed = config.get("test_passed")

        combined_new = f"{new_output}\n{new_stderr}"

        # Check if original error is gone
        original_fixed = original_error.lower() not in combined_new.lower()

        # Check for new errors
        error_indicators = ["error", "exception", "traceback", "failed"]
        new_errors = any(ind in combined_new.lower() for ind in error_indicators)

        # If test result provided, use it
        if test_passed is not None:
            original_fixed = test_passed
            new_errors = not test_passed

        # Calculate confidence
        confidence = 0.5
        if original_fixed and not new_errors:
            confidence = 0.9
        elif original_fixed and new_errors:
            confidence = 0.3
        elif not original_fixed:
            confidence = 0.1

        if test_passed is True:
            confidence = 1.0
        elif test_passed is False:
            confidence = 0.0

        # Generate verification details
        details = []
        if original_fixed:
            details.append("Original error no longer appears")
        else:
            details.append("Original error still present")

        if new_errors:
            details.append("WARNING: New errors detected in output")

        if expected_behavior and expected_behavior.lower() in new_output.lower():
            details.append("Expected behavior observed")
            confidence = min(confidence + 0.1, 1.0)

        return {
            "fix_verified": original_fixed and not new_errors,
            "original_fixed": original_fixed,
            "new_errors": new_errors,
            "confidence": confidence,
            "verification_details": "; ".join(details),
        }


class ErrorAggregatorNode(BaseNode):
    """
    Aggregate errors across multiple iterations for reporting.
    """

    type = "error-aggregator"
    name = "Debug: Error Summary"
    category = "Coding"
    description = "Aggregate and summarize errors across debug iterations"
    icon = "summarize"
    color = "#17A2B8"  # Info blue

    inputs = [
        NodeField(
            name="current_errors", label="Current Errors", type=FieldType.JSON, required=False
        ),
        NodeField(
            name="historical_errors", label="Historical Errors", type=FieldType.JSON, required=False
        ),
        NodeField(
            name="fixes_attempted", label="Fixes Attempted", type=FieldType.JSON, required=False
        ),
        NodeField(
            name="iteration", label="Iteration", type=FieldType.NUMBER, required=False, default=0
        ),
    ]

    outputs = [
        NodeField(name="total_errors_found", label="Total Errors Found", type=FieldType.NUMBER),
        NodeField(name="errors_resolved", label="Errors Resolved", type=FieldType.NUMBER),
        NodeField(name="errors_remaining", label="Errors Remaining", type=FieldType.NUMBER),
        NodeField(name="fix_success_rate", label="Fix Success Rate", type=FieldType.NUMBER),
        NodeField(name="most_common_errors", label="Most Common Errors", type=FieldType.JSON),
        NodeField(name="report", label="Debug Report", type=FieldType.TEXT),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        current_errors = config.get("current_errors", [])
        historical_errors = config.get("historical_errors", [])
        fixes_attempted = config.get("fixes_attempted", [])
        iteration = int(config.get("iteration", 0))

        # Combine all errors
        all_errors = list(historical_errors) + list(current_errors)
        total_found = len(all_errors)

        # Count error types
        error_type_counts = {}
        for error in all_errors:
            if isinstance(error, dict):
                etype = error.get("type", "Unknown")
            else:
                etype = str(error)[:50]
            error_type_counts[etype] = error_type_counts.get(etype, 0) + 1

        # Sort by frequency
        most_common = sorted(error_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Calculate stats
        errors_remaining = len(current_errors)
        errors_resolved = total_found - errors_remaining

        fixes_count = len(fixes_attempted) if fixes_attempted else iteration
        fix_success_rate = (errors_resolved / fixes_count * 100) if fixes_count > 0 else 0

        # Generate report
        report_lines = [
            f"=== Debug Summary (Iteration {iteration}) ===",
            f"Total errors found: {total_found}",
            f"Errors resolved: {errors_resolved}",
            f"Errors remaining: {errors_remaining}",
            f"Fix success rate: {fix_success_rate:.1f}%",
            "",
            "Most common error types:",
        ]

        for etype, count in most_common:
            report_lines.append(f"  - {etype}: {count}")

        if current_errors:
            report_lines.append("")
            report_lines.append("Current errors:")
            for err in current_errors[:5]:
                if isinstance(err, dict):
                    report_lines.append(
                        f"  - {err.get('type', 'Error')}: {err.get('message', '')[:80]}"
                    )
                else:
                    report_lines.append(f"  - {str(err)[:80]}")

        return {
            "total_errors_found": total_found,
            "errors_resolved": errors_resolved,
            "errors_remaining": errors_remaining,
            "fix_success_rate": round(fix_success_rate, 1),
            "most_common_errors": [{"type": t, "count": c} for t, c in most_common],
            "report": "\n".join(report_lines),
        }


class ConditionalBranchNode(BaseNode):
    """
    Branch workflow based on conditions - essential for debug loops.
    """

    type = "conditional-branch"
    name = "Flow: Conditional Branch"
    category = "Coding"
    description = "Branch workflow based on boolean condition"
    icon = "call_split"
    color = "#6C757D"

    inputs = [
        NodeField(name="condition", label="Condition", type=FieldType.BOOLEAN, required=True),
        NodeField(name="true_value", label="Value if True", type=FieldType.JSON, required=False),
        NodeField(name="false_value", label="Value if False", type=FieldType.JSON, required=False),
    ]

    outputs = [
        NodeField(name="result", label="Result", type=FieldType.JSON),
        NodeField(name="branch", label="Branch Taken", type=FieldType.STRING),
        NodeField(name="is_true", label="Condition is True", type=FieldType.BOOLEAN),
        NodeField(name="is_false", label="Condition is False", type=FieldType.BOOLEAN),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        condition = config.get("condition", False)
        true_value = config.get("true_value", {"branch": "true"})
        false_value = config.get("false_value", {"branch": "false"})

        if condition:
            return {
                "result": true_value,
                "branch": "true",
                "is_true": True,
                "is_false": False,
            }
        else:
            return {
                "result": false_value,
                "branch": "false",
                "is_true": False,
                "is_false": True,
            }


class WaitNode(BaseNode):
    """
    Wait/delay node for retry loops.
    """

    type = "wait"
    name = "Flow: Wait"
    category = "Coding"
    description = "Pause workflow execution for specified duration"
    icon = "hourglass_empty"
    color = "#6C757D"

    inputs = [
        NodeField(
            name="seconds", label="Wait Seconds", type=FieldType.NUMBER, required=True, default=1
        ),
        NodeField(
            name="pass_through", label="Pass Through Data", type=FieldType.JSON, required=False
        ),
    ]

    outputs = [
        NodeField(name="data", label="Data", type=FieldType.JSON),
        NodeField(name="waited", label="Seconds Waited", type=FieldType.NUMBER),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        seconds = float(config.get("seconds", 1))
        pass_through = config.get("pass_through", {})

        await asyncio.sleep(seconds)

        return {
            "data": pass_through,
            "waited": seconds,
        }
