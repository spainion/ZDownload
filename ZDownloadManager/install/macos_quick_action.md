## macOS Quick Action for ZDownloadManager

To add a Finder Quick Action that sends files to ZDownloadManager:

1. Open **Automator** and create a new **Quick Action**.
2. Set **Workflow receives current** to *files or folders* in *Finder*.
3. From the **Actions** library search for **Run Shell Script** and drag it to the workflow.
4. Set **Shell** to `/bin/bash` and **Pass input** to `as arguments`.
5. Replace the script body with:

   ```bash
   for f in "$@"; do
       python3 -m zdownloadmanager.cli "$f"
   done
   ```

6. Save the Quick Action with a name like **Send to ZDownloadManager**.

After saving, right‑click any file in Finder and choose **Quick Actions → Send to ZDownloadManager** to organise it via the command line.
