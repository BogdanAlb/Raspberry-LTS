from csv import DictReader


with open('data.csv', 'r') as file:
    reader = DictReader(file)
    for row in reader:
        print(row)