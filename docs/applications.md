# Finding the applications

Applications run **inside Whonix Workstation**, not as macOS apps. Start Gateway first, then Workstation. Choose **PERSISTENT Mode | USER Session** at the boot menu and open the LXQt application menu. The **SYSMAINT** session shows a maintenance panel for updates and administration instead of the ordinary application desktop.

Workstation's packaged desktop entries include:

| Application | Purpose |
|---|---|
| Tor Browser | Web browsing; the preview explicitly includes the official **16.0a14 ARM64 alpha** |
| Tor Browser Downloader | Whonix download/signature-verification integration; configured for alpha in this preview |
| System Check | Whonix system/network checks; unsupported-platform notices must remain visible |
| QTerminal | Terminal |
| PCManFM-Qt | File manager |
| KeePassXC | Password manager |
| Metadata Cleaner | Remove supported file metadata |
| Electrum | Bitcoin wallet; not part of the browser validation and not configured with any account |
| FeatherPad | Text editor |
| VLC | Media player; this VM configuration disables audio |
| System Maintenance Panel | Maintenance in the SYSMAINT session |

Gateway is the routing/control VM. Use Workstation for browsing and ordinary applications. Documentation/forum menu links need a working browser in Workstation.

The standard browser launcher remains `torbrowser`, so Whonix's Gateway proxy and stream-isolation integration are preserved. Launch it through the menu or run `torbrowser` in Workstation's terminal. Do not run the bundled Tor daemon separately or bypass the Whonix launcher.

The package/application inventories attached to the prerelease list the exact image contents. A launcher being present does not prove the application has been individually tested. Consult the release validation record for the checks actually completed.

Gateway also includes Anon Connection Wizard, Tor Control Panel, Onion Circuits and Nyx, plus Tor stop/restart/configuration tools. These belong to Gateway's control role; they are not missing Workstation browser applications.
