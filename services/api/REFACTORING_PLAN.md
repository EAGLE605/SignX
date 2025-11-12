# Rigorous Linting and Refactoring Plan

## Current State
- Started with: 4949 errors
- Auto-fixed (safe): 2360 errors
- Auto-fixed (unsafe): 994 errors
- **Remaining: 1572 errors**

## Priority Categories

### Phase 1: Critical Security & Correctness (Priority: HIGH)
- [ ] 259 TID252 - Convert relative imports to absolute imports
- [ ] 58 BLE001 - Replace blind except with specific exception handling
- [ ] 22 DTZ003 - Replace datetime.utcnow() with timezone-aware alternatives
- [ ] 13 S110 - Fix try-except-pass silent failures
- [ ] 1 S307 - Review suspicious eval() usage
- [ ] 2 S608 - Review hardcoded SQL expressions

### Phase 2: Type Safety & Code Quality (Priority: MEDIUM)
- [ ] 50 ANN401 - Replace Any types with specific types
- [ ] 48 ARG001 - Remove or mark unused function arguments
- [ ] 24 ARG002 - Remove or mark unused method arguments
- [ ] 29 B904 - Add exception chaining (from e)
- [ ] 22 B008 - Review Depends() in defaults (justified for FastAPI)
- [ ] 22 E402 - Review lazy imports (some justified)

### Phase 3: Code Complexity (Priority: MEDIUM)
- [ ] 166 PLR2004 - Extract magic values to named constants
- [ ] 17 C901 - Refactor complex functions (cyclomatic complexity > 10)
- [ ] 26 PLR0913 - Reduce functions with too many arguments
- [ ] 8 PLR0912 - Reduce functions with too many branches
- [ ] 8 PLR0915 - Reduce functions with too many statements

### Phase 4: Code Organization (Priority: LOW)
- [ ] 259 TID252 - Fix relative imports
- [ ] 71 PLC0415 - Review import-outside-top-level
- [ ] 47 INP001 - Add __init__.py for namespace packages

### Phase 5: Documentation (Priority: LOW)
- [ ] 29 D103 - Add docstrings to public functions
- [ ] 18 D100 - Add module docstrings
- [ ] 14 D107 - Add __init__ docstrings
- [ ] 7 D101 - Add class docstrings

### Phase 6: Style Improvements (Priority: DEFER)
- [ ] 250 E501 - Line too long (already ignored, acceptable)
- [ ] 45 N806 - Variable naming conventions
- [ ] 20 D401 - Docstring imperative mood
- [ ] 14 ERA001 - Remove commented-out code
- [ ] 14 FIX002/TD002/TD003 - TODO improvements

## Execution Strategy

1. **Automated where possible**: Use ruff --fix for safe changes
2. **Systematic manual fixes**: Fix by category, starting with critical
3. **Test after each phase**: Run pytest to ensure no regressions
4. **Commit frequently**: One commit per phase or major category
5. **Update ruff config**: Add justified ignores with documentation

## Notes
- Some ignores are justified (E501, B008 for FastAPI patterns)
- Focus on security and correctness first
- Documentation can be added incrementally
- Some complexity may require architectural refactoring
