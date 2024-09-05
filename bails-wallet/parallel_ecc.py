import multiprocessing
import codex32

CHARSET = codex32.CHARSET

# Define your is_valid function here
def is_valid(candidate):
    data = [CHARSET.find(x) for x in candidate[3:]]
    if codex32.ms32_verify_checksum(data):
        return candidate


def generate_corrections(invalid_str):
    # Function to generate and check corrections
    # Try insertions, deletions, and substitutions
    corrections = set()
    corrections.add(invalid_str)

    # Generate insertions
    for i in range(3, len(invalid_str) + 1):
        for char in CHARSET:
            new_str = invalid_str[:i] + char + invalid_str[i:]
            corrections.add(new_str)

    # Generate deletions
    for i in range(3, len(invalid_str)):
        new_str = invalid_str[:i] + invalid_str[i + 1:]
        corrections.add(new_str)

    # Generate substitutions
    for i in range(3, len(invalid_str)):
        for char in CHARSET:
            if char != invalid_str[i]:
                new_str = invalid_str[:i] + char + invalid_str[i + 1:]
                corrections.add(new_str)

    return corrections

#print(is_valid('ms10testsxxxxxxxxxxxxxxxxxxxxxxxxxx4nzvca9cmczlw'))
#exit()
# Example usage
invalid_str = 'ms10testsxxxxxxxxxxxxxxxxxxxxxxx4nzvca9cmczlw'

# Use multiprocessing to check if corrections are valid
pool = multiprocessing.Pool()
candidates = generate_corrections(invalid_str)
valid_corrections = pool.imap_unordered(is_valid, candidates)

# Find the closest valid correction
for correction in valid_corrections:
    if correction:
        print("Invalid String:", invalid_str)
        print("First Valid Correction:", correction)
        exit()  # Exit the loop as soon as the first valid correction is found

new_candidates = pool.imap_unordered(generate_corrections, candidates)
for candidate in new_candidates:
    valid_new_corrections = pool.imap_unordered(is_valid, candidate)
    for correction in valid_new_corrections:
        if correction:
            print("Invalid String:", invalid_str)
            print("First Valid Correction:", correction)
            break  # Exit the loop as soon as the first valid correction is found