# Bugs and Issues Found During Test Development

## Overview
While developing comprehensive pytest coverage and fixing test failures, several bugs and undesirable behaviors were discovered in the application code.

---

## 1. ChatWidget.handle_validation_result() - Incorrect attempt_number When Validation Passes

**Date Found:** 2025-01-XX  
**Status:** ✅ **FIXED**  
**Location:** [src/game_ai/ui/chat_widget.py](src/game_ai/ui/chat_widget.py#L323-L336)

**Issue:** The `attempt_number` field was always set to `4 - max_validation_attempts` even when validation passed (no errors). This meant that when a game file validated successfully on the first try, `attempt_number` would be 1 instead of 0.

**Bug Code:**
```python
result = {
    'should_retry': False,
    'error_text': '',
    'fix_prompt': '',
    'attempt_number': 4 - max_validation_attempts  # ❌ Always calculated
}

if not errors:
    # Validation passed
    return result
```

**Impact:** Misleading metrics - successful validations would show as "attempt 1" instead of "no attempts needed".

**Fix:**
```python
result = {
    'should_retry': False,
    'error_text': '',
    'fix_prompt': '',
    'attempt_number': 0  # Will be set correctly if there are errors
}

if not errors:
    # Validation passed - attempt_number stays 0
    return result

# We have errors - calculate actual attempt number
result['attempt_number'] = 4 - max_validation_attempts
```

**How Found:** Created unit tests for validation loop logic. Test expected `attempt_number=0` when no errors, but got `attempt_number=1`.

---

## 2. EditorWidget.set_content() - Potential Crash if Not Mounted

**Location:** [src/game_ai/ui/editor_widget.py](src/game_ai/ui/editor_widget.py#L82-L95)

**Issue:** The `set_content()` method calls `query_one("#editor-title", Static)` without checking if the widget is mounted. This will crash if called before the widget is added to the app.

```python
# This always calls query_one, even if widget not mounted
title = self.query_one("#editor-title", Static)
title.update("Game File Editor - Strategic Form (.nfg)")
```

**Impact:** Runtime crash if set_content() is called before widget is fully initialized in the app.

**Fix Suggestion:** Add a guard similar to the visualization_widget check:
```python
if self._content_widget:  # or similar mounted state check
    title = self.query_one("#editor-title", Static)
    title.update("Game File Editor - Strategic Form (.nfg)")
```

---

## 3. SessionManager API Inconsistency

**Location:** [src/game_ai/chat/session_manager.py](src/game_ai/chat/session_manager.py)

**Issue:** Inconsistent return types across methods make error handling unpredictable:
- `save_session()` returns `bool`
- `load_session()` returns `dict | None`  
- `list_sessions()` returns `list`

**Impact:** Inconsistent error handling patterns across the codebase. Some places check for bool, others check for None, others check for dict with "success" key.

**Fix Suggestion:** Standardize on a uniform API pattern:
```python
# Option 1: Always return dict with status
{"success": bool, "data": Any, "error": str | None}

# Option 2: Always return result object
class SessionResult:
    success: bool
    data: Any
    error: str | None
```

---

## 4. Strict PyGambit Format Requirements

**Location:** Throughout validator and solver modules

**Issue:** PyGambit is extremely sensitive to game file formatting:
- Payoffs MUST be on separate lines (not inline)
- Integer vs decimal format matters in some contexts
- EFG terminal nodes need outcome labels (even empty `""`)
- Whitespace/indentation matters

**Example of valid format:**
```
NFG 1 R "Game Name"
{ "Player 1" "Player 2" }
{ 2 2 }

1 2 3 4
```

**Example of invalid format that looks correct:**
```
NFG 1 R "Game Name" { "Player 1" "Player 2" } { 2 2 } 1 2 3 4
```

**Impact:** User frustration when AI generates games in slightly different formats that look valid but fail parsing. Error messages from pygambit are cryptic (e.g., "Expected numerical payoff at line 1:69").

**Fix Suggestions:**
1. Add format validation/normalization layer before passing to pygambit
2. Improve error messages to be more user-friendly
3. Add format examples to AI prompts
4. Post-process AI-generated games to normalize format

---

## 5. Missing Error Field Handling

**Location:** [src/game_ai/ai/game_builder.py](src/game_ai/ai/game_builder.py#L159)

**Issue:** While we fixed `response.get("sources", [])`, other response fields like `game_file`, `explanation`, etc. could also be missing from the API response. The code should defensively handle all optional fields.

**Current code:**
```python
return {
    "explanation": response["explanation"],  # Could be missing
    "game_file": response["game_file"],      # Could be missing
    "sources": response.get("sources", []),  # Fixed
    "metadata": response["metadata"]          # Could be missing
}
```

**Fix Suggestion:**
```python
return {
    "explanation": response.get("explanation", ""),
    "game_file": response.get("game_file", ""),
    "sources": response.get("sources", []),
    "metadata": response.get("metadata", {})
}
```

---

## 5. Original Issue: Empty game_file Problem (ROOT CAUSE)

**Location:** Gemini API structured output behavior

**Issue:** The **empty `game_file` problem** that started this debugging session is inherent to how Gemini's structured output works. The API only validates JSON schema syntax, not semantic content. It can legally return:
```json
{
  "game_file": "",
  "explanation": "Here's the game...",
  "sources": [],
  "metadata": {}
}
```

Even though the schema says `game_file` is a string, there's no way to force it to be non-empty.

**Current Status:** Debug logs help diagnose the issue but don't fix the root cause.

**Fix Suggestions:**

### Option A: Post-Response Validation with Retry
```python
response = await gemini_client.generate_response(...)
if not response.get("game_file", "").strip():
    # Retry with more explicit prompt
    response = await gemini_client.generate_response(
        history + [{"role": "user", "content": "CRITICAL: The game_file field was empty. Please provide the complete game file content in NFG or EFG format."}],
        use_structured_output=True
    )
```

### Option B: Enhanced Prompting
Add to system prompt or generation prompt:
```
CRITICAL REQUIREMENT: The game_file field MUST contain the complete game in valid NFG or EFG format. 
Do NOT leave it empty. If you cannot generate a valid game file, explain why in the explanation field 
but still include a placeholder or template in game_file.
```

### Option C: Fallback Extraction
```python
if not response.get("game_file", "").strip():
    # Try to extract game from explanation field
    explanation = response.get("explanation", "")
    game_file = extract_game_from_text(explanation)
    if game_file:
        response["game_file"] = game_file
```

### Option D: Remove Structured Output for /generate
Use natural language response and extract the game file using regex/parsing since structured output doesn't guarantee semantic correctness anyway.

---

## 6. Test Coverage Revealed Real Formatting Issues

**Impact:** Multiple tests initially failed because the test game formats didn't match pygambit's strict expectations. This strongly suggests the application generates invalid games frequently in production.

**Evidence:**
- Initial test games used inline format → all failed
- Games without decimal points → failed  
- EFG games without outcome labels → failed
- Games with leading whitespace → failed

**User Impact:** Users probably experience frequent validation/solving failures that they can't understand or fix.

**Fix Suggestions:**
1. Add comprehensive format validation before attempting to parse/solve
2. Provide AI with strict format examples and templates
3. Add format auto-correction for common mistakes
4. Show users example valid formats when validation fails
5. Add a "format checker" command that explains what's wrong

---

## Priority Recommendations

### High Priority (User-Facing)
1. **Fix empty game_file issue** (Option A or B above)
2. **Improve pygambit format error messages** - users need to understand what's wrong
3. **Add format validation/normalization** - prevent cryptic errors

### Medium Priority (Code Quality)
4. **Standardize SessionManager API** - improves maintainability
5. **Add defensive .get() calls** - prevents crashes on unexpected API responses

### Low Priority (Edge Cases)
6. **Fix EditorWidget mount check** - rare edge case but easy fix

---

## Testing Status

All 53 tests now pass after fixing these issues in the test suite:
- ✅ 4 gemini_client tests
- ✅ 5 game_builder tests  
- ✅ 3 command_handler tests
- ✅ 7 validator tests
- ✅ 7 solver tests
- ✅ 8 session_manager tests
- ✅ 11 editor_widget tests
- ✅ 8 visualization_widget tests

The test fixes revealed the actual API surface and behavior, documenting the issues above.
