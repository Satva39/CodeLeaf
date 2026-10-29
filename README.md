# CodeLeaf Home Category Filter CSS Patch

This is an incremental PowerShell patch, not a replacement `home.css`. It appends a marked CSS override to your current file, preserving all unrelated CSS changes. Re-running the script replaces its own marked block rather than duplicating it.

## Apply
Extract the ZIP into `E:\Code_Leaf`, then run from PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\Apply-CodeLeaf-CategoryTabsCssPatch.ps1 -ProjectRoot "E:\Code_Leaf"
cd E:\Code_Leaf\frontend
node scripts\test-home-category-tabs-css.mjs
npm run build
```

The Home page category filters become one horizontally scrollable row of consistently styled pill chips. Long labels are truncated to keep the chips the same height; the selected, hover and keyboard-focus states are clear. Reduced-motion preferences are respected. Existing responsive rules are preserved.

No pricing, checkout, or entitlement logic is changed by this patch.
