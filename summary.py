def generate_summary(data):
    total = 0
    category_total = {}

    for row in data:
        if len(row) < 2:
            continue

        amount = int(row[0])
        category = row[1]

        total += amount

        if category in category_total:
            category_total[category] += amount
        else:
            category_total[category] = amount

    return total, category_total