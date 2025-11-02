# PE Fix Scripts - Documentation

## Overview

This directory contains the automated scripts for fixing critical PE calculation errors in SignX-Studio to achieve ASCE 7-22 and IBC 2024 compliance.

## Scripts

### 1. execute_pe_fixes.ps1 (Master Script)
**Purpose:** Orchestrates the entire fix process
**Runtime:** ~5 minutes
**Usage:**
```powershell
.\execute_pe_fixes.ps1 [-SkipBackup] [-SkipTests] [-Verbose]
```

**Parameters:**
- `-SkipBackup`: Skip backup creation (not recommended)
- `-SkipTests`: Skip validation tests (not recommended)  
- `-Verbose`: Enable detailed output

**What it does:**
1. Verifies environment and required files
2. Creates timestamped backups
3. Applies all three calculation fixes
4. Adds input validation layer
5. Runs validation test suite
6. Generates comprehensive report

### 2. fix_critical_calculations.ps1
**Purpose:** Core calculation fixes for wind, loads, and foundation
**Called by:** execute_pe_fixes.ps1 (automatically)

**Fixes Applied:**
- Wind formula (ASCE 7-22 Eq. 26.10-1)
- Load combinations (IBC 2024 Section 1605.2.1)
- Foundation calculation (IBC 2024 Eq. 18-1)

### 3. add_input_validation.ps1
**Purpose:** Adds engineering validation to all inputs
**Called by:** execute_pe_fixes.ps1 (automatically)

**Validations Added:**
- Wind speed ranges (90-200 mph)
- Height limits (15-60 ft standard)
- Soil bearing capacity (1500-12000 psf)
- Material properties (ASTM grades)

### 4. validate_calculations.py
**Purpose:** Python test suite verifying all fixes
**Called by:** execute_pe_fixes.ps1 (automatically)
**Can run standalone:** 
```bash
python scripts/validate_calculations.py
```

**Tests:**
- Wind velocity pressure: 26.4 psf
- Design wind pressure: 26.9 psf
- Load combinations: 7 present
- Foundation depth: 19.9 ft
- Error magnitude verification

## File Modifications

The scripts modify these core files:

| File | Changes |
|------|---------|
| `services/api/src/apex/domains/signage/asce7_wind.py` | Wind formula correction |
| `services/api/src/apex/domains/signage/single_pole_solver.py` | Load combinations |
| `services/api/src/apex/domains/signage/solvers.py` | Foundation calculation |
| `services/api/src/apex/domains/signage/input_validation.py` | New validation module |

## Backup Structure

Backups are created in:
```
backups/
└── pe_fixes_YYYYMMDD_HHMMSS/
    ├── asce7_wind.py
    ├── solvers.py
    └── single_pole_solver.py
```

## Reports Generated

| Report | Location | Content |
|--------|----------|---------|
| Execution Log | `PE_FIX_REPORT_[timestamp].log` | Complete execution trace |
| Test Results | Console output | Pass/fail for each test |
| Summary | Console output | Critical changes applied |

## Error Handling

The scripts include comprehensive error handling:

- **Missing Files:** Stops execution, lists missing files
- **Backup Failure:** Stops execution, preserves original files
- **Fix Application Error:** Stops execution, suggests manual review
- **Test Failure:** Completes but warns, provides detailed failure info
- **Python Not Found:** Provides installation instructions

## Common Issues & Solutions

### Issue: "Missing required files"
**Solution:** Ensure running from SignX-Studio root directory
```powershell
cd C:\Scripts\SignX-Studio
.\scripts\execute_pe_fixes.ps1
```

### Issue: "Python command not found"
**Solution:** Ensure Python 3.8+ is installed and in PATH
```powershell
python --version  # Should show 3.8 or higher
```

### Issue: "Access denied"
**Solution:** Run PowerShell as Administrator or check file permissions

### Issue: "Tests failing"
**Solution:** Review test output, ensure all 3 fixes were applied correctly

## Manual Rollback

If needed (returns to non-compliant state):

```powershell
# Find your backup timestamp
ls backups/

# Restore files
$backup = "backups/pe_fixes_20251102_143022"
Copy-Item "$backup\*.py" "services/api/src/apex/domains/signage/" -Force
```

**WARNING:** Rollback restores code violations. Only use if absolutely necessary.

## Validation

After execution, verify:

1. **Check Report:** Review `PE_FIX_REPORT_[timestamp].log`
2. **Run Tests Manually:**
   ```bash
   python scripts/validate_calculations.py
   ```
3. **Verify Changes:**
   ```powershell
   # Check wind formula
   Select-String "0.00256" services/api/src/apex/domains/signage/asce7_wind.py
   
   # Check load combinations
   Select-String "IBC_LOAD_COMBINATIONS" services/api/src/apex/domains/signage/single_pole_solver.py
   
   # Check foundation equation
   Select-String "IBC.*Equation 18-1" services/api/src/apex/domains/signage/solvers.py
   ```

## Code References

All fixes comply with:
- **ASCE 7-22:** Minimum Design Loads for Buildings
- **IBC 2024:** International Building Code
- **AISC 360-22:** Structural Steel Buildings Specification

Specific references:
- Wind: ASCE 7-22 Equation 26.10-1
- Loads: IBC 2024 Section 1605.2.1
- Foundation: IBC 2024 Equation 18-1

## Support

For issues or questions:
1. Check `PE_FIX_REPORT_[timestamp].log`
2. Review `docs/PE_CALCULATION_FIXES.md`
3. Run validation manually
4. Contact PE reviewer if calculations unclear

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-02 | Initial release with 3 critical fixes |

---

**Remember:** These fixes are REQUIRED for PE stamp compliance. The previous calculations violate building codes and must not be used.
