# Troubleshooting Index

Quick reference to find the right troubleshooting guide for your issue.

## I'm Getting a NameError

### `NameError: name 'scenario_emergency_procurement' is not defined`

**Quick Fix**: [QUICKFIX_NAMEERROR.txt](QUICKFIX_NAMEERROR.txt)

**Step-by-Step Fix for Your Code**: [FIX_YOUR_LOCAL_CODE.md](FIX_YOUR_LOCAL_CODE.md)

**Complete Guide**: [BUGFIX_EMERGENCY_PROCUREMENT.md](BUGFIX_EMERGENCY_PROCUREMENT.md)

**Prevention Guide**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

### Other NameError Issues

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Section: "Generic Fix Template"

## I Have a Different Version of the Code

**Migration Guide**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

Shows how to:
- Fix undefined variable errors
- Migrate from custom version to repository version
- Apply best practices
- Debug similar issues

## Download/Installation Issues

**Download Guide**: [DOWNLOAD.md](DOWNLOAD.md)

**Quick Start**: [QUICKSTART.md](QUICKSTART.md)

**How to Download**: [HOW_TO_DOWNLOAD.txt](HOW_TO_DOWNLOAD.txt)

## General Troubleshooting

**README Troubleshooting Section**: [README.md](README.md#troubleshooting)

Covers:
- Solver not found
- Infeasible solutions
- Slow performance
- NameError/undefined variables
- Version compatibility

## Documentation Overview

| Document | Purpose | Best For |
|----------|---------|----------|
| QUICKFIX_NAMEERROR.txt | Immediate one-line fix | Quick reference |
| FIX_YOUR_LOCAL_CODE.md | Step-by-step local fix | Following exact steps |
| BUGFIX_EMERGENCY_PROCUREMENT.md | Complete fix with examples | Understanding the issue |
| MIGRATION_GUIDE.md | General patterns & migration | Learning best practices |
| README.md | Full project documentation | Complete reference |
| QUICKSTART.md | Getting started guide | New users |
| DOWNLOAD.md | Download instructions | Installation |

## Quick Decision Tree

```
Do you have a NameError?
├─ YES: Is it about 'scenario_emergency_procurement'?
│   ├─ YES: Go to QUICKFIX_NAMEERROR.txt or FIX_YOUR_LOCAL_CODE.md
│   └─ NO: Go to MIGRATION_GUIDE.md (Generic patterns)
└─ NO: What's your issue?
    ├─ Download: Go to DOWNLOAD.md
    ├─ Getting started: Go to QUICKSTART.md
    ├─ General issues: Go to README.md (Troubleshooting section)
    └─ Migration: Go to MIGRATION_GUIDE.md
```

## Error Code Quick Reference

| Error | Document | Section |
|-------|----------|---------|
| NameError: name 'scenario_emergency_procurement' | FIX_YOUR_LOCAL_CODE.md | Complete guide |
| NameError: name 'scenario_*' | MIGRATION_GUIDE.md | Generic Fix Template |
| Model infeasible | README.md | Troubleshooting |
| Solver not found | README.md | Troubleshooting |
| AttributeError | MIGRATION_GUIDE.md | Check Existence |
| KeyError | MIGRATION_GUIDE.md | Use Default Values |

## Still Need Help?

1. **Read the specific guide** for your error
2. **Check README.md** for general troubleshooting
3. **Review examples** in the repository
4. **Run tests** to verify your setup: `pytest test_optimization.py -v`
5. **Open an issue** with details if problem persists

## Pro Tips

💡 **Tip 1**: Always read the error message carefully - the line number tells you where to fix

💡 **Tip 2**: Use the repository version if you're having multiple issues

💡 **Tip 3**: Test after each fix to isolate the problem

💡 **Tip 4**: Keep a backup before making changes

💡 **Tip 5**: Add comments explaining your fixes for future reference

---

**Start Here**: If you just got an error, check QUICKFIX_NAMEERROR.txt first!
