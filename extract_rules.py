import csv
import pprint

with open("C:\\Users\\deepe\\Downloads\\fendeddesk rule - Sheet1.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        if "Profit Target" in str(row) or "Drawdown" in str(row) or "Leverage" in str(row) or "Fee" in str(row):
            print("---")
            # print non empty cols
            print([c for c in row if c.strip()])
