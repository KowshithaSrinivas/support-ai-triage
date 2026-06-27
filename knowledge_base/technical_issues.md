# Technical Issues (App & Export)

## Mobile app crashes after update
Known issue pattern: crashes opening a specific section right after a version update are usually caused by a stale local cache conflicting with new schema. Standard fix:
1. Ask the customer to fully close the app (not just background it).
2. Clear app cache (Android: Settings > Apps > [App Name] > Storage > Clear Cache). Note: this does not delete account data.
3. Reopen the app. If it still crashes, uninstall and reinstall.
4. If the crash persists, escalate to engineering with device model, OS version, and app version — this may indicate a real regression bug rather than a cache issue.

## CSV / data export failing silently
If an export "fails silently" (no error shown, but no file produced), check:
- Whether the dataset being exported exceeds the 50,000-row limit for synchronous export (larger exports should use the async export endpoint and arrive via email).
- Whether the customer's browser is blocking the download as a pop-up.
For enterprise customers reporting repeated export failures, treat as high priority — this can indicate a backend timeout issue affecting multiple accounts, and the support lead should be notified to check for a wider outage pattern.

## API rate limits
Standard plan: 60 requests/minute. Enterprise plan: 100 requests/minute by default, but can be increased on request. Requests for rate limit increases from enterprise customers should be forwarded to the solutions engineering team with the customer's use case and required throughput.
