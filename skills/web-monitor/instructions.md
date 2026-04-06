# Web Monitor

Monitor a web page for changes by periodically fetching it and comparing with the previous snapshot.

## Steps

1. Fetch the target URL using the helper script
2. Compare with the previously stored snapshot (if any)
3. Report any differences to the user
4. Save the current version as the new snapshot
