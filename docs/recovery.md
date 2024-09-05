# BailsWallet Recovery Information

BailsWallet creates extended public keys for the coordinator following [slip-0132](https://github.com/satoshilabs/slips/blob/master/slip-0132.md) to encode the extended public key. BailsWallet supports taproot, native and nested segwit for single sig and multisig.

Derivation paths for standard script types for mainnet:

- Single Sig
	- Native Taproot
		- Derivation Path: m/86'/0'/0'
		- Script Type: P2WPKH
		- Public Key Encoding: 0x0488B21E - xpub
	- Native Segwit
		- Derivation Path: m/84'/0'/0'
		- Script Type: P2WPKH
		- Public Key Encoding: 0x0488B21E - xpub
	- Nested Segwit
		- Derivation Path: m/49'/0'/0'
		- Script Type: P2WPKH in P2SH
		- Public Key Encoding: 0x0488B21E - xpub
	- Legacy Pubkey Hash
        - Derivation Path: m/49'/0'/0'
		- Script Type: P2PKH
		- Public Key Encoding: 0x0488B21E - xpub	    
- Multisig
	- Native Segwit
		- Derivation Path: m/48'/0'/0'/2'
		- Script Type: P2WSH
		- Public Key Encoding: 0x0488B21E - xpub
	- Nested Segwit
		- Derivation Path: m/48'/0'/0'/1'
		- Script Type: P2WSH in P2SH
		- Public Key Encoding: 0x0488B21E - xpub

Changing the network settings from main to test in BailsWallet will change the public key encoding and derivation path following [slip-0132](https://github.com/satoshilabs/slips/blob/master/slip-0132.md) standards.

Related Standards:
- [bip-0032](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki)
- [bip-0044](https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki)
- [bip-0048](https://github.com/bitcoin/bips/blob/master/bip-0048.mediawiki)
- [bip-0049](https://github.com/bitcoin/bips/blob/master/bip-0049.mediawiki)
- [bip-0084](https://github.com/bitcoin/bips/blob/master/bip-0084.mediawiki)
- [bip-0086](https://github.com/bitcoin/bips/blob/master/bip-0086.mediawiki)
