
import csv
from collections import Counter, defaultdict

INPUT_FILE = "data/external_human_dataset/llm_pairwise_results.csv"
OUTPUT_FILE = "data/external_human_dataset/pairwise_analysis_summary.csv"



def get_human_majority(annotations):
    votes = [vote.strip() for vote in annotations.split("|")]

    # Convert human labels into the same format as LLM choices
    votes = [
        "A" if vote.lower() == "codea"
        else "B" if vote.lower() == "codeb"
        else "Tie"
        for vote in votes
    ]

    counts = Counter(votes)
    highest_count = max(counts.values())

    winners = [
        label for label, count in counts.items()
        if count == highest_count
    ]

    if len(winners) != 1:
        return "Tie"

    return winners[0]


def convert_gt_choice(value):
    value = str(value).strip()

    if value == "0":
        return "A"
    elif value == "1":
        return "B"

    return "Unknown"


def calculate_agreement(rows, human_field):
    total = len(rows)
    correct = sum(
        row["llm_choice"] == row[human_field]
        for row in rows
    )

    percentage = (correct / total * 100) if total else 0

    return correct, total, percentage


def print_confusion_matrix(rows, human_field, title):
    labels = ["A", "B", "Tie"]

    matrix = {
        human: {llm: 0 for llm in labels}
        for human in labels
    }

    for row in rows:
        human = row[human_field]
        llm = row["llm_choice"]

        if human in labels and llm in labels:
            matrix[human][llm] += 1

    print(f"\n{title}")
    print("Rows = Human | Columns = LLM")
    print(f"{'Human/LLM':<12}{'A':<10}{'B':<10}{'Tie':<10}")

    for human in labels:
        print(
            f"{human:<12}"
            f"{matrix[human]['A']:<10}"
            f"{matrix[human]['B']:<10}"
            f"{matrix[human]['Tie']:<10}"
        )


def main():

    with open(INPUT_FILE, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        rows = [
            row for row in reader
            if row["status"] == "SUCCESS"
        ]

    # Prepare human labels
    for row in rows:
        row["human_majority"] = get_human_majority(
            row["human_annotations"]
        )

        row["human_gt"] = convert_gt_choice(
            row["human_gt_choice"]
        )

        row["category"] = row["task_id"].split("/")[0]

    print("=" * 55)
    print("LLM-AS-A-JUDGE: PAIRWISE HUMAN ALIGNMENT ANALYSIS")
    print("=" * 55)

    print(f"\nTotal successful comparisons: {len(rows)}")

    # Comparison 1: Human annotation majority
    correct, total, percentage = calculate_agreement(
        rows, "human_majority"
    )

    print("\n1. LLM vs HUMAN ANNOTATION MAJORITY")
    print(f"Agreements: {correct}/{total}")
    print(f"Disagreements: {total - correct}/{total}")
    print(f"Agreement percentage: {percentage:.2f}%")

    print_confusion_matrix(
        rows, "human_majority",
        "CONFUSION MATRIX: HUMAN MAJORITY"
    )

    # Comparison 2: Dataset ground-truth preference
    valid_gt_rows = [
        row for row in rows
        if row["human_gt"] in ["A", "B"]
    ]

    correct, total, percentage = calculate_agreement(
        valid_gt_rows, "human_gt"
    )

    print("\n2. LLM vs DATASET GT_CHOICE")
    print(f"Agreements: {correct}/{total}")
    print(f"Disagreements: {total - correct}/{total}")
    print(f"Agreement percentage: {percentage:.2f}%")

    print_confusion_matrix(
        valid_gt_rows, "human_gt",
        "CONFUSION MATRIX: GT_CHOICE"
    )

    # Comparison by dataset category
    print("\n3. AGREEMENT BY DATASET CATEGORY")

    categories = defaultdict(list)

    for row in rows:
        categories[row["category"]].append(row)

    for category, category_rows in categories.items():

        majority_correct, majority_total, majority_pct = (
            calculate_agreement(category_rows, "human_majority")
        )

        gt_rows = [
            row for row in category_rows
            if row["human_gt"] in ["A", "B"]
        ]

        gt_correct, gt_total, gt_pct = (
            calculate_agreement(gt_rows, "human_gt")
        )

        print(f"\n{category}")
        print(
            f"Human majority agreement: "
            f"{majority_correct}/{majority_total} "
            f"({majority_pct:.2f}%)"
        )
        print(
            f"GT choice agreement: "
            f"{gt_correct}/{gt_total} "
            f"({gt_pct:.2f}%)"
        )

    # Save summary
    summary_rows = []

    for reference, reference_field in [
        ("Human annotation majority", "human_majority"),
        ("Dataset gt_choice", "human_gt")
    ]:

        comparison_rows = [
            row for row in rows
            if row[reference_field] in ["A", "B", "Tie"]
        ]

        correct, total, percentage = calculate_agreement(
            comparison_rows, reference_field
        )

        summary_rows.append({
            "human_reference": reference,
            "agreements": correct,
            "disagreements": total - correct,
            "total": total,
            "agreement_percentage": round(percentage, 2)
        })

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "human_reference",
                "agreements",
                "disagreements",
                "total",
                "agreement_percentage"
            ]
        )

        writer.writeheader()
        writer.writerows(summary_rows)

    print("\n" + "=" * 55)
    print("ANALYSIS COMPLETED")
    print(f"Summary saved to: {OUTPUT_FILE}")
    print("=" * 55)


if __name__ == "__main__":
    main()
