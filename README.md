# product-lca-carbon-calculator
Calculate the units of carbon required for every input of an item's production lifecycle

## Claude Code Hooks Setup

This project uses development automation for development workflow automation. To initialize hooks with absolute paths:

```bash
# First time setup (or after cloning)
npm run setup
```

This runs `scripts/init-claude.py` which generates `settings.local.json` with absolute hook paths, preventing "No such file or directory" errors when changing directories.

**Why absolute paths?** Hooks with relative paths fail when you `cd backend` or work in subdirectories. Absolute paths work regardless of current working directory.

See `scripts/README.md` for details.
