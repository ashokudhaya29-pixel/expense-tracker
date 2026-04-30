def generate_summary(data):
    total = 0
    category_total = {}

    for row in data:
        if len(row) < 2:
            continue

        salary = int(row[0])
        category = row[1]

        total += salary

        if category in category_total:
            category_total[category] += salary
        else:
            category_total[category] = salary

    return total, category_total