
# Standard function names for each programming problem.
# Multiple names are allowed because Qwen generated variations.

FUNCTION_MAP = {
    "P01": ["is_prime"],
    "P02": ["reverse_string"],
    "P03": ["factorial","calculate_factorial"],
    "P04": ["is_palindrome"],
    "P05": [
        "sort_list_of_integers",
        "sort_list",
        "bubble_sort",
        "selection_sort",
        "insertion_sort"
    ],
    "P06": ["find_largest_element"],
    "P07": ["find_duplicates"],
    "P08": ["binary_search"],
    "P09": ["linear_search"],
    "P10": [
        "generate_fibonacci",
        "fibonacci",
        "fibonacci_series"
    ],
    "P11": ["count_vowels"],
    "P12": ["are_anagrams"],
    "P13": ["gcd","find_gcd"],
    "P14": ["remove_duplicates"],
    "P15": ["merge_sorted_arrays"],
    "P16": ["is_balanced_parentheses","is_balanced"],
    "P17": ["find_second_largest"],
    "P18": [
        "count_word_frequency",
        "word_frequency"
    ],
    "P19": [
        "matrix_multiply",
        "multiply_matrices"
    ],
    "P20": [
        "validate_password_strength",
        "is_valid_password",
        "validate_password"
    ]
}

# Benchmark conventions
BENCHMARK_RULES = {
    "P04": "Case-sensitive palindrome checking",
    "P12": "Case-insensitive anagram checking",
    "P20": (
        "Minimum 8 characters, uppercase, lowercase, "
        "digit and special character"
    )
}

print("BENCHMARK CONFIGURATION LOADED")
print("Problem mappings:", len(FUNCTION_MAP))
print("Special benchmark rules:", len(BENCHMARK_RULES))
