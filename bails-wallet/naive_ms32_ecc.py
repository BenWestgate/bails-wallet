import multiprocessing

import codex32
from multiprocessing import Pool
CHARSET=codex32.CHARSET
def find_closest_valid_codex32(codex32_str, insert=[], delete=[], substitute=[], valid_header='ms1', valid_length=48, invalid_index=[]):
    """Find the closest valid codex32 string using an iterative approach."""
    global heading
    global invalid_indices
    heading = valid_header
    invalid_indices = invalid_index
    if codex32.decode("ms", codex32_str) != (None, None, None, None):
        return codex32_str
    pos = codex32_str.rfind("1")

    def generate_edits(candidate):  # TODO make 3 separate functions for each type of edit for a huge speed-up.
        # Generate all possible edits (insertion, deletion, substitution)
        edits = set()

        for i in range(len(heading), len(candidate)):
            # Deletions
            if delete[search_phase]:
                edits.add(candidate[:i] + candidate[i + 1:])

            # Substitutions:
            if substitute[search_phase]:
                for char in CHARSET:
                    if char != candidate[i]:
                        if not (i == 8 and char in invalid_indices):
                            edits.add(candidate[:i] + char + candidate[i + 1:])
            # Insertions
            if insert[search_phase]:
                for char in CHARSET:
                    if not (i == 7 and char in invalid_indices):
                        edits.add(candidate[:i + 1] + char + candidate[i + 1:])

        # Add insertion at the end of the candidate string
        if insert[search_phase]:
            for char in CHARSET:
                edits.add(candidate[:len(candidate)] + char)
        return edits

    candidates = {codex32_str}  # Start with the given string as the first candidate
    for search_phase in range(0, len(delete)):
        new_candidates = set()
        for candidate in candidates:
            # Generate all possible edits (insertion, deletion, substitution)
            edits = generate_edits(candidate)
            for new_candidate in edits:
                if new_candidate not in new_candidates:
                    new_candidates.add(new_candidate)
        candidates = new_candidates

        # Check if any of the new candidates are valid codex32 strings
        pool = multiprocessing.Pool()
        valid_corrections = pool.imap_unordered(is_valid, candidates)
        for correction in valid_corrections:
            if correction:
                print("Invalid String:", codex32_str)
                print("First Valid Correction:", correction)
                exit()  # Exit the loop as soon as the first valid correction is found

    return None  # If no valid codex32 string is found within the error correction capabilities


def is_valid(candidate):
    data = [CHARSET.find(x) for x in candidate[3:]]
    if codex32.ms32_verify_checksum(data):
        return candidate

def find_correction(invalid_codex32_str, valid_length=48, valid_header='ms1', invalid_index=[]):
    input_length = len(invalid_codex32_str)
    if valid_length:
        length_syn = input_length - valid_length
    else:
        if input_length > 45 and input_length < 55:
            closest_valid_codex32 = find_correction(invalid_codex32_str, 48, valid_header, invalid_index)
        elif input_length > 71 and input_length < 81:
            closest_valid_codex32 = find_correction(invalid_codex32_str, 74, valid_header, invalid_index)
        elif input_length > 124 and input_length < 134:
            closest_valid_codex32 = find_correction(invalid_codex32_str, 127, valid_header, invalid_index)
        if closest_valid_codex32:
            return closest_valid_codex32
        search_order = [[[False, True], [True, False], [False, False]],
                        [[True, False], [False, False], [False, True]],
                        [[False, False], [True, False], [False,  True]],
                        [[False, False, True], [True, True, False], [False, False, False]],
                        [[False, False, False], [True, True, False], [False, False, True]],
                        [[False, False], [False, False], [True, True]],
                        [[True]*2, [False]*2, [False]*2],
                        [[False]*2, [True]*2, [False]*2],
                        [[False]*3, [True]*3, [False]*3]]
        for error_type in search_order:
            insertion = error_type[0]
            deletion = error_type[1]
            substitution = error_type[2]
            closest_valid_codex32 = find_closest_valid_codex32(invalid_codex32_str, insertion, deletion, substitution, valid_header, invalid_index)
            if closest_valid_codex32:
                return closest_valid_codex32

    # parameter order  (insertion, deletion, substitution)
    if length_syn == -2:
        closest_valid_codex32 = find_closest_valid_codex32(invalid_codex32_str, [True]*2, [False]*2, [False]*2, valid_header, invalid_index)
    elif length_syn == -1:
        closest_valid_codex32 = find_closest_valid_codex32(invalid_codex32_str, [True, False], [False, False], [False, True], valid_header, invalid_index)
    elif length_syn == 0:
        closest_valid_codex32 = find_closest_valid_codex32(invalid_codex32_str, [False, True], [True, False], [False, False], valid_header, invalid_index)
        if not closest_valid_codex32:
            closest_valid_codex32= find_closest_valid_codex32(invalid_codex32_str, [False, False], [False, False], [True, True], valid_header, invalid_index)
    elif length_syn == 1:
        closest_valid_codex32 = find_closest_valid_codex32(invalid_codex32_str, [False, False], [True, False], [False,  True], valid_header, invalid_index)
        if not closest_valid_codex32:
            closest_valid_codex32 = find_closest_valid_codex32(invalid_codex32_str, [False, False, True], [True, True, False], [False, False, False], valid_header, invalid_index)
    elif length_syn == 2:
        closest_valid_codex32 = find_closest_valid_codex32(invalid_codex32_str, [False, False, False], [True, True, False], [False, False, True], valid_header, invalid_index)
    elif 7 > length_syn > 2:
        closest_valid_codex32 = find_closest_valid_codex32(invalid_codex32_str, [False]*length_syn, [True]*length_syn, [False]*length_syn, valid_header, invalid_index)

    if closest_valid_codex32:
        return closest_valid_codex32
    else:
        return None

print(find_correction('MS12NAMEA320ZYXWVUTSRQPNMLKJHGFEDC999999AXRPP870HKKQRM'.lower(), 48, 'ms1', []))