import codex32
import multiprocessing

CHARSET=codex32.CHARSET


def substitute(string, index, char):
    return string[:index] + char + string[index + 1:]

def find_closest_valid_codex32(codex32_str, valid_header='ms1', valid_length=48, invalid_index=[]):
    import codex32

    CHARSET = codex32.CHARSET

    def fill_erasures(codex32_str):
        erasures = codex32_str.count('?')

        if erasures > 8:
            # Cannot correct more than 8 erasures, return original string
            return codex32_str

        original_checksum = codex32_str[-13:]  # Extract the original checksum
        data_part = codex32_str[:-13]  # Extract the data part without the checksum

        # Initialize a list to store candidate corrected strings
        candidates = [data_part]

        for i in range(erasures):
            new_candidates = []

            for candidate in candidates:
                for char in CHARSET:
                    new_candidate = candidate.replace('?', char, 1)  # Replace the first '?' with a bech32 character
                    new_candidates.append(new_candidate)

            candidates = new_candidates

        # Now, candidates contain all possible corrected strings
        corrected_strings = [candidate + original_checksum for candidate in candidates]

        # You can further validate the corrected strings using your validation function if needed
        valid_corrected_strings = [s for s in corrected_strings if codex32.decode('ms', s) != (None, None, None, None)]

        return valid_corrected_strings

    # Example usage
    codex32_string = 'ms10testsx?xxxx?xx?xxxxxxxxxxxxx?xx4nzvca9cmczlw'
    corrected_strings = fill_erasures(codex32_string)

    # Print the corrected strings
    for corrected_string in corrected_strings:
        print(corrected_string)

    exit()


    if codex32.decode("ms", codex32_str) != (None, None, None, None):
        return codex32_str




    candidates = {codex32_str}  # Start with the given string as the first candidate

    pool = multiprocessing.Pool()  # Use all available CPU cores
    for search_phase in range(0, len(delete)):
        new_candidates = set()
        results = pool.imap_unordered(worker, candidates)
        for result in results:
            new_candidates.update(result)
        candidates = new_candidates

        # Check if any of the new candidates are valid codex32 strings
        for candidate in candidates:
            print(candidate)
            if valid_length and len(candidate) != valid_length:
                pass
            elif codex32.decode("ms", candidate) != (None, None, None, None):
                return candidate

    return None  # If no valid codex32 string is found within the error correction capabilities

def gen_insert(candidate, pos):
    for char in CHARSET:
        if not (pos == 7 and char in invalid_indices):
            return candidate[:pos + 1] + char + candidate[pos + 1:]

def gen_subsitution(candidate, pos):
    for char in CHARSET:
        if char != candidate[pos]:
            if not (pos == 8 and char in invalid_indices):
                return candidate[:pos] + char + candidate[pos + 1:]

def gen_delete(candidate, pos):
    return candidate[:pos] + candidate[pos + 1:]

def worker(candidate):
    # Worker function for parallel processing
    def generate_edits(candidate):

        pool2 = multiprocessing.Pool()  # Use all available CPU cores
        results = pool.map(worker, range(len(heading), len(candidate)))


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

    new_candidates = set()
    edits = generate_edits(candidate)
    for new_candidate in edits:
        if new_candidate not in new_candidates:
            new_candidates.add(new_candidate)
    return new_candidates

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

find_closest_valid_codex32('ms10test?xxxxxxxxx?xxxxx??xxxxxxxxx4nzvca9cmczlw')
