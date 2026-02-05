# Download Instructions

## 📥 How to Download This Project

There are multiple ways to download the Wildfire-Resilient Supply Network Optimization project. Choose the method that works best for you.

---

## Method 1: Download as ZIP File (Recommended for Beginners)

This is the easiest method if you just want to download and run the project without using Git.

### Steps:

1. **Visit the GitHub repository**:
   - Go to: https://github.com/satasouji-svg/Code

2. **Click the Code button**:
   - Look for the green **"Code"** button near the top-right of the page (next to "Add file")
   
3. **Download ZIP**:
   - Click on **"Download ZIP"** from the dropdown menu
   - Your browser will download a file named `Code-main.zip` (or similar)

4. **Extract the ZIP file**:
   - **Windows**: Right-click the ZIP file → "Extract All..." → Choose destination
   - **Mac**: Double-click the ZIP file (it extracts automatically)
   - **Linux**: Right-click → "Extract Here" or use command: `unzip Code-main.zip`

5. **Navigate to the folder**:
   ```bash
   cd Code-main  # Or wherever you extracted it
   ```

6. **Install and run**:
   ```bash
   pip install -r requirements.txt
   python main.py --mode demo
   ```

---

## Method 2: Clone with Git (Recommended for Developers)

If you have Git installed and want to track updates or contribute, use this method.

### Steps:

1. **Open terminal/command prompt**

2. **Clone the repository**:
   ```bash
   git clone https://github.com/satasouji-svg/Code.git
   ```

3. **Navigate to the directory**:
   ```bash
   cd Code
   ```

4. **Install and run**:
   ```bash
   pip install -r requirements.txt
   python main.py --mode demo
   ```

### Updating with Git:
To get the latest updates:
```bash
cd Code
git pull origin main
```

---

## Method 3: Download Specific Release

Download a stable, versioned release of the project.

### Steps:

1. **Visit the Releases page**:
   - Go to: https://github.com/satasouji-svg/Code/releases

2. **Choose a version**:
   - Browse available releases (if any are published)
   - Click on the release you want

3. **Download assets**:
   - Download the source code (ZIP or tar.gz)
   - Extract and follow installation instructions

---

## Method 4: GitHub CLI (For Advanced Users)

If you have GitHub CLI (`gh`) installed:

```bash
gh repo clone satasouji-svg/Code
cd Code
```

---

## Method 5: Download Individual Files

If you only need specific files:

1. Navigate to the file on GitHub
2. Click the "Raw" button
3. Right-click → "Save As..." or press `Ctrl+S`

---

## After Download: Next Steps

Once you've downloaded the project using any method above:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run quick demo** (takes ~1 minute):
   ```bash
   python main.py --mode demo
   ```

3. **Run tests** to verify everything works:
   ```bash
   pytest test_optimization.py -v
   ```

4. **Check the documentation**:
   - Read [README.md](README.md) for full documentation
   - See [QUICKSTART.md](QUICKSTART.md) for a 5-minute guide
   - View [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for complete details

---

## Troubleshooting Download Issues

### Problem: "Permission denied" when extracting
**Solution**: Make sure you have write permissions in the target directory.

### Problem: ZIP file is corrupted or won't extract
**Solution**: 
1. Try downloading again
2. Use a different extraction tool (7-Zip, WinRAR, etc.)
3. Try the Git clone method instead

### Problem: Can't find the Code button on GitHub
**Solution**: Make sure you're on the main repository page at https://github.com/satasouji-svg/Code

### Problem: Git clone fails with "Permission denied"
**Solution**: 
1. Make sure Git is installed: `git --version`
2. Check your internet connection
3. Try HTTPS clone URL instead of SSH

---

## File Size Information

- **Repository size**: ~500 KB (source code only)
- **After installing dependencies**: ~200-300 MB (includes all Python packages)
- **Generated results** (after running): Varies (typically 1-5 MB for outputs)

---

## What's Included in the Download?

When you download the project, you'll get:

### Core Modules (Python files):
- `config.py` - Network configuration
- `scenario_gen.py` - Scenario generation
- `model.py` - Optimization model
- `solver.py` - Solver interface
- `validation.py` - Validation framework
- `reporter.py` - Result reporting
- `visualizer.py` - Visualization tools
- `experiments.py` - Experimental design
- `main.py` - Main execution script
- `examples.py` - Custom examples
- `test_optimization.py` - Test suite

### Documentation:
- `README.md` - Complete documentation
- `QUICKSTART.md` - Quick start guide
- `PROJECT_SUMMARY.md` - Project summary
- `DOWNLOAD.md` - This file

### Configuration:
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore rules

---

## Alternative Download Sources

If GitHub is not accessible:

1. **Download from a mirror** (if available)
2. **Request a copy** by opening an issue on the repository
3. **Use a VPN** if GitHub is blocked in your region

---

## License Information

This project is provided for research and educational purposes. Please check the repository for specific license terms before using in production or commercial settings.

---

## Getting Help

If you have trouble downloading:

1. **Check GitHub Status**: https://www.githubstatus.com/
2. **Open an Issue**: https://github.com/satasouji-svg/Code/issues
3. **Check Documentation**: Make sure you're following the correct steps above

---

## Quick Reference

| Method | Best For | Difficulty | Requires |
|--------|----------|------------|----------|
| Download ZIP | Beginners, one-time use | Easy | Web browser only |
| Git Clone | Developers, updates | Medium | Git installed |
| GitHub CLI | Power users | Medium | GitHub CLI |
| Releases | Stable versions | Easy | Web browser only |

**Most users should use Method 1 (Download ZIP)** for the quickest and easiest download experience.

---

**Ready to start?** After downloading, jump to the [QUICKSTART.md](QUICKSTART.md) for a 5-minute getting started guide!
