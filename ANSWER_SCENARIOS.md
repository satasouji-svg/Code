# Answer: How Many Scenarios?

## 🎯 Quick Answer

**The system uses 20 scenarios by default.**

Each scenario has equal probability: **5%** (1/20 = 0.05)

## 📍 Where to Find This Information

### Option 1: Run the Info Script (Easiest)
```bash
python info.py
```

Output shows:
```
📊 SCENARIOS
----------------------------------------------------------------------
  Number of Scenarios: 20
  Probability per Scenario: 0.0500 (5.00%)
```

### Option 2: Read the FAQ
See [SCENARIOS_FAQ.md](SCENARIOS_FAQ.md) for complete details on:
- What scenarios are
- How to change the count
- Performance recommendations
- Impact on solution quality

### Option 3: Check README Quick Facts
See [README.md](README.md) - look for the "Quick Facts" table near the top:

| Feature | Default Value | Configurable? |
|---------|---------------|---------------|
| **Number of Scenarios** | **20** | ✅ Yes |

### Option 4: View Source Code
See [config.py](config.py) line 113:
```python
self.num_scenarios = 20  # Default: 20 scenarios
```

## 🔧 How to Change

Edit `config.py`:
```python
class ModelParameters:
    def __init__(self):
        # ... other parameters ...
        self.num_scenarios = 50  # Change to your desired value
```

## 📊 What You Get with Different Counts

| Scenarios | Solve Time | Use Case |
|-----------|------------|----------|
| 3-10 | < 5 sec | Quick testing |
| **20** ✓ | 10-30 sec | **Development (default)** |
| 50-100 | 1-5 min | Production |
| 100-500 | 5-30 min | Research |

## ✨ Recent Documentation Additions

We've added several resources to make this information easy to find:

1. ✅ **SCENARIOS_FAQ.md** - Comprehensive FAQ about scenarios
2. ✅ **info.py** - Configuration query script
3. ✅ **README.md Quick Facts** - Prominent display of scenario count
4. ✅ **TROUBLESHOOTING_INDEX.md** - Common questions section

## 🚀 Quick Start

```bash
# View current configuration
python info.py

# Run demo with default 20 scenarios
python main.py --mode demo

# Read comprehensive FAQ
cat SCENARIOS_FAQ.md
```

## 📚 Related Documentation

- [SCENARIOS_FAQ.md](SCENARIOS_FAQ.md) - Complete scenario documentation
- [README.md](README.md) - Main project documentation
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [config.py](config.py) - Source code configuration

---

**Last Updated:** 2026-02-05  
**Quick Answer:** **20 scenarios** (default, configurable)  
**Check with:** `python info.py`
