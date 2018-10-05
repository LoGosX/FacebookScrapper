import sys
import json
import csv
from collections import Counter
from itertools import chain

class LikeItem:

    def __init__(self, text, url, type_of_site):
        self.text = text
        self.url = url
        self.type = type_of_site

    def __eq__(self, other):
        return self.url == other.url

    def __hash__(self):
        return hash(self.url)

def main():
    args = sys.argv
    if len(args) == 3:
        output_path = args[2]
        inputh_path = args[1]
    elif len(args) == 2:
        output_path = "./"
        inputh_path = args[1]
    else:
        print('No input file. Aborting')
        return
        
    with open(inputh_path, 'r') as input_file:
        data = json.load(input_file)

    with open(output_path, "w", newline = "") as output_file:
        f = csv.writer(output_file, delimiter = '\t')
        f.writerow(['Text', 'Type', 'Count', 'Url'])
        
        likes = Counter(LikeItem(like['text'], like['href'], like['type']) for like in chain.from_iterable(user['likes'] for user in data) if like['type'])
        for like, count in likes.items():
            f.writerow([like.text, like.type, count, like.url])


if __name__ == '__main__':
    main()
