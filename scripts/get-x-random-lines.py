import random, argparse

# print a list of randomly selected line numbers, separated by
# newlines. X lines are chosen from a range of 1 to num_lines, where X
# is provided as a second argument (how_many) by the user.

argparser = argparse.ArgumentParser(description="""Print a list of randomly 
selected line numbers, separated by newlines. X lines are chosen from a 
range of 1 to num_lines, where X is provided as a second argument (how_many) 
by the user.""")

argparser.add_argument('num_lines', type=int)
argparser.add_argument('how_many', type=int)
args = argparser.parse_args()


for linenum in sorted(random.sample(xrange(1,args.num_lines), args.how_many)):
    print(linenum)


