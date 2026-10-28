# Arabic TV – auto-updated M3U for TiviMate

Creates one M3U playlist, with Syria first and the remaining Arab countries in order. Uses iptv-org's country playlists, deduplicates identical stream URLs, and preserves channel metadata. **No subscription bypass, no guarantee that each stream plays or is licensed in your region.**

## Setup (once)

1. Create a **public** GitHub repository, e.g. `arabic-iptv-auto`.
2. Upload `build.py`, `README.md`, and `.github/workflows/update.yml` with the same directory structure.
3. Under repository **Settings → Actions → General → Workflow permissions**, select **Read and write permissions** (if available), and save.
4. Open **Actions → Update Arabic TV playlist → Run workflow**. Wait for a successful run.
5. The playlist URL will be:

   `https://raw.githubusercontent.com/YOUR_USERNAME/arabic-iptv-auto/main/arabic-tv.m3u`

   Replace `YOUR_USERNAME` with your GitHub username. If the default branch isn't `main`, replace `main` too.
6. Add that URL to **TiviMate → Add playlist → M3U playlist** and enable periodic playlist updates in TiviMate settings.

GitHub Actions runs daily (approximately; schedules can be delayed). If any country source is unavailable, the workflow fails without replacing the previous list. This approach does **not** test stream playback or independently validate broadcast rights.

Data source: https://github.com/iptv-org/iptv
