from datetime import time


def clean():
    with open("NASDAQ.txt", "r") as file:
        nasdeq = []
        for line in file:
            sep = '\t'
            cleaned = line.split(sep, 1)[0]
            nasdeq += [cleaned]

    with open("NYSE.txt", "r") as file:
        nyse = []
        for line in file:
            sep = '\t'
            cleaned = line.split(sep, 1)[0]
            nyse += [cleaned]

    combined = nyse + nasdeq
    combined_list = list(set(combined))
    sorted_list = sorted(combined_list)

    with open("NASDAQandNYSE.txt", "w") as file:
        for ticker in sorted_list:
            file.write(ticker)
            file.write('\n')
        file.close()


clean()