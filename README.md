# bails-wallet
Auditable Python Gtk implementation for creating & importing [codex32](https://github.com/BlockstreamResearch/codex32) seed backups to Bitcoin Core. Work-in-progress.


L1 (BETA) Scope:

Create:
- Checks the Bitcoin RPC is responsive, option is not available if it is not.
- Will grab an xprv from a temporary bitcoin core encrypted wallet for entropy.
- Will allow the user to add entropy and display unconditionally the entropy above in an inconspicuous way.
- Will allow selection of threshold, ID (default is BIP32 fingerpirnt), share indices (default is deterministic cryptographic) and quantity.
- Will allow backing up either the codex32 string or the codex32 QR code, which is the same data.
- Confirmation will be agnostic whether a string is typed or a QR code was scanned.
- Runs Recover and forgets the seed (remembers fingerprint and header to detect a rare mismatch) to make the user practice recovering.

[Recover](https://github.com/BlockstreamResearch/codex32/blob/master/docs/wallets.md) (complies with codex32 import docs):
- Accepts either QR or typing the codex32.
- If ran after Create, will verify the share headers and fingerprint match what was created.
- Performs best effort (up to 4 substitutions, 8 erasures, additions/deletions) error correction on codex32 strings
- Rejects invalid shares and QRs
- Produces the xprv / descriptor after success.
- Allows producing multiple descriptors using BIP85 for multiple wallets including bruteforcing decoys with the same fingerprint.
- The stateless savings wallet will be the root BIP32 seed, spending, panic mode and decoy wallets will be BIP85 children xprvs to protect the savings.

L2 Scope:

Create:
- Displays compact 21x21 CodexQR codes when compatible with the other codex32 backup parameters selected.
- Accepts existing codex32 strings for changing backup parameters without sweeping funds or replacing every share. (may name this Modify in the GUI)

Recover:
- Scans 21x21 CodexQR codes and detects mismatched QRs and shares and fills in the missing data of the codex32 string on a best effort basis.
- Uses a PSBT or watch-only wallet to improve the error detection of compact Codex32 QRs as well as to suggest a likely ID of shares/QRs to look for.
- Possibly allow encrypting and saving the recovery progress.
- Displays a QR of the public descriptor for creating an online watch-only wallet.

https://github.com/BenWestgate/Bails/issues/57#issuecomment-2018659295
