def compute_age_groups(queryset):
    buckets = [
        ("<13", 0, 12),
        ("13-17", 13, 17),
        ("18-24", 18, 24),
        ("25-34", 25, 34),
        ("35+", 35, 200),
    ]
    counts = {
        label: 0
        for label, _, _ in buckets
    }

    for age in queryset.values_list(
        "age",
        flat=True,
    ):
        if age is None:
            continue

        for label, start, end in buckets:
            if start <= age <= end:
                counts[label] += 1
                break

    return [
        {
            "label": label,
            "total": total,
        }
        for label, total in counts.items()
    ]
