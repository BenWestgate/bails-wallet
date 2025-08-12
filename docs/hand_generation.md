(09:22:51 AM) benwestgate: speaking of by hand, the CRC-7 I use to create the index + padding is only ~128 lines of no carry binary long division, probably takes <10 extra minutes to make a "codexQR-compatible" codex32 share.
(09:25:05 AM) andytoshi: interesting. lmk if you every try it (i guess it would require at least one new volvelle)
(09:26:34 AM) benwestgate: andytoshi: https://www.youtube.com/watch?v=kscjEvjTVBI
(09:28:28 AM) andytoshi: benwestgate: ok, but that's 3 bech32 characters
(09:29:20 AM) benwestgate: It will take 2 or 3 sheets of paper: A normal 81/2" x 11" page may contain a maximum of 66 lines, with 6 lines per inch. 
(09:29:35 AM) andytoshi: yeah, ok, i believe you

(09:35:14 AM) benwestgate: may have missed messages sent after I shared the lines per sheet of notebook paper.
(09:35:14 AM) benwestgate: I'm looking for some to try it on a 128-bit number
(09:45:48 AM) andytoshi: benwestgate: nope, no messages while you were dropped
(09:46:02 AM) andytoshi: well, actually i can't tell when you actually dropped, just when the server noticed
(09:46:16 AM) andytoshi: last thing i said was "maybe with some lookup tables you can do the whole thing directly in bech32 chars"
(09:49:12 AM) benwestgate: ok, i just spent 3 minutes writing down the seed, landscape 11x8.5 paper. I think it's going to be hard to keep track of alignment
(09:49:12 AM) benwestgate: I could barely fit the divisor + 128 bits
(09:49:40 AM) andytoshi: i have a sheet somewhere that has some alignment helpers
(09:50:14 AM) andytoshi: hmm, maybe i didn't publish them
(09:50:29 AM) andytoshi: it has ticks every 5 bits and ticks every 11 bits
(09:50:34 AM) andytoshi: to help with converting from bech32 to bip39 words
(09:53:01 AM) benwestgate: Yes it would be helpful.
(09:53:01 AM) benwestgate: 5mm graph paper, 136 cells wide for the divisor and data is 26.6" so it's doable
(09:55:36 AM) andytoshi: benwestgate: page 22 of https://github.com/apoelstra/codex32/tree/bip39 ... though that is for a 264-bit seed
(09:55:44 AM) andytoshi: but you could use just the first half of it
(09:57:02 AM) benwestgate: This would work too: 36" x 120" graph paper roll, 1/4" grid, it looks like it's long enough too.
(09:58:27 AM) andytoshi: hehe
(09:59:20 AM) benwestgate: Not worth the $38 bucks per seed if gonna burn it.  Better to print it, tape two lengthwise if you can't write small enough and wear reading glasses.
(10:02:27 AM) benwestgate: vertical space is going to be the quotient row, divisor ) entropy row, then 2 lines per 1 in the quotient, which is 120 bits, so 122 vertical lines is the average length
(10:03:00 AM) andytoshi: i have some 8.5x11 graph paper which has a 10x10 grid per inch. for binary you could probably use each cell for a character
(10:03:08 AM) andytoshi: so that's 110 height ... so close
(10:04:06 AM) benwestgate: 99.9% of seeds will have less than 76 1's in the quotient
(10:06:07 AM) benwestgate: Yeah it's custom printed graph paper 11"/136 = 0.08"/grid or 12.5 lines/1"
(10:07:35 AM) andytoshi: mine was a little pricey but it was at hobby lobby so at least easy to get
(10:07:47 AM) benwestgate: Then you could tape two width wise and have 212.5 cells for the XORs
(10:07:58 AM) andytoshi: yeah, that's a good idea
(10:09:16 AM) benwestgate: I'll make a note of the grid needed in my repo and try it when I'm done.
(10:09:38 AM) andytoshi: sounds good
(10:14:14 AM) benwestgate: It will be just on the border of what is legible:
(10:14:14 AM) benwestgate: 12.5 characters per inch is equivalent to 5.8 pt font.
(10:14:14 AM) benwestgate: Older adults probably can't do with the naked eye, but college students may be able.
(10:15:12 AM) andytoshi: well if it's only zeros and ones maybe it's ok
(10:17:53 AM) benwestgate: yeah, it helps. I can read my 128-bits pretty easily, more likely to miscount streaks >5 than anything, but that won't matter while you're dividing since you're comparing 8-9 bits at a time.
(10:24:19 AM) andytoshi: yeah, miscounting streaks was a big difficulty when i was doing bech32->bip39 conversions

(09:35:14 AM) benwestgate: may have missed messages sent after I shared the lines per sheet of notebook paper.
(09:35:14 AM) benwestgate: I'm looking for some to try it on a 128-bit number
(09:45:48 AM) andytoshi: benwestgate: nope, no messages while you were dropped
(09:46:02 AM) andytoshi: well, actually i can't tell when you actually dropped, just when the server noticed
(09:46:16 AM) andytoshi: last thing i said was "maybe with some lookup tables you can do the whole thing directly in bech32 chars"
(09:49:12 AM) benwestgate: ok, i just spent 3 minutes writing down the seed, landscape 11x8.5 paper. I think it's going to be hard to keep track of alignment
(09:49:12 AM) benwestgate: I could barely fit the divisor + 128 bits
(09:49:40 AM) andytoshi: i have a sheet somewhere that has some alignment helpers
(09:50:14 AM) andytoshi: hmm, maybe i didn't publish them
(09:50:29 AM) andytoshi: it has ticks every 5 bits and ticks every 11 bits
(09:50:34 AM) andytoshi: to help with converting from bech32 to bip39 words
(09:53:01 AM) benwestgate: Yes it would be helpful.
(09:53:01 AM) benwestgate: 5mm graph paper, 136 cells wide for the divisor and data is 26.6" so it's doable
(09:55:36 AM) andytoshi: benwestgate: page 22 of https://github.com/apoelstra/codex32/tree/bip39 ... though that is for a 264-bit seed
(09:55:44 AM) andytoshi: but you could use just the first half of it
(09:57:02 AM) benwestgate: https://www.amazon.com/Geyer-Instructional-Products-Blueprints-Floorplans
(09:57:02 AM) benwestgate: This would work too: 36" x 120" graph paper roll, 1/4" grid, it looks like it's long enough too.
(09:58:27 AM) andytoshi: hehe
(09:59:20 AM) benwestgate: Not worth the $38 bucks per seed if gonna burn it.  Better to print it, tape two lengthwise if you can't write small enough and wear reading glasses.
(10:02:27 AM) benwestgate: vertical space is going to be the quotient row, divisor ) entropy row, then 2 lines per 1 in the quotient, which is 120 bits, so 122 vertical lines is the average length
(10:03:00 AM) andytoshi: i have some 8.5x11 graph paper which has a 10x10 grid per inch. for binary you could probably use each cell for a character
(10:03:08 AM) andytoshi: so that's 110 height ... so close
(10:04:06 AM) benwestgate: 99.9% of seeds will have less than 76 1's in the quotient
(10:06:07 AM) benwestgate: Yeah it's custom printed graph paper 11"/136 = 0.08"/grid or 12.5 lines/1"
(10:07:35 AM) andytoshi: mine was a little pricey but it was at hobby lobby so at least easy to get
(10:07:47 AM) benwestgate: Then you could tape two width wise and have 212.5 cells for the XORs
(10:07:58 AM) andytoshi: yeah, that's a good idea
(10:09:16 AM) benwestgate: I'll make a note of the grid needed in my repo and try it when I'm done.
(10:09:38 AM) andytoshi: sounds good
(10:14:14 AM) benwestgate: It will be just on the border of what is legible:
(10:14:14 AM) benwestgate: 12.5 characters per inch is equivalent to 5.8 pt font.
(10:14:14 AM) benwestgate: Older adults probably can't do with the naked eye, but college students may be able.
(10:15:12 AM) andytoshi: well if it's only zeros and ones maybe it's ok
(10:17:53 AM) benwestgate: yeah, it helps. I can read my 128-bits pretty easily, more likely to miscount streaks >5 than anything, but that won't matter while you're dividing since you're comparing 8-9 bits at a time.
(10:24:19 AM) andytoshi: yeah, miscounting streaks was a big difficulty when i was doing bech32->bip39 conversions
(10:45:26 AM) benwestgate: well at least here only window 8-9 matters not 11.
(10:45:26 AM) benwestgate: A smaller CRC-5 could set just the index, at cost of detection abilities, but you need to repeat w/ a CRC-2 for padding. or do zeros. Probably faster to set both in one division.
(10:45:26 AM) benwestgate: If speed were the only goal: index = sum(payload symbols) % 32
(10:45:26 AM) benwestgate: But I'm almost positive that one leaks too much info about the secret at k-1 shares.
(10:45:52 AM) andytoshi: yeah, i would'nt make any compromises for the sake of hand-computability here
(10:49:33 AM) benwestgate: The main part, that will give hand computing pain is, deriving n > k shares with this checksum. It's trial and error.  There are 30 chances at k=2, but only 1/128 chance per chance it accidentally validates
(10:53:13 AM) benwestgate: So given a master seed, k=2, only 1 in 5 of these fancy share will derive any shares with valid crc.
(10:57:26 AM) benwestgate: can't make a tiny codexQR of share unless the crc7 validates. But it's fast to find a set on a desktop and this doubles as the cryptographic shuffle for the share indexes :)
(11:08:27 AM) andytoshi: yeah i see