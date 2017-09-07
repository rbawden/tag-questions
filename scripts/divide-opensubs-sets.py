# calculate set divisions in opensubs corpus
import argparse
import gzip
import os

argparser=argparse.ArgumentParser()
argparser.add_argument('filmlines_file')
argparser.add_argument('train_percent', type=float)
argparser.add_argument('dev1_percent', type=float)
argparser.add_argument('dev2_percent', type=float)
argparser.add_argument('test_percent', type=float)
argparser.add_argument('train_outfile')
argparser.add_argument('dev1_outfile')
argparser.add_argument('dev2_outfile')
argparser.add_argument('test_outfile')
args = argparser.parse_args()

train = args.train_percent
dev1 = args.dev1_percent
dev2 = args.dev2_percent
test = args.test_percent


if train+dev1+dev2+test != 100:
    os.sys.stderr.write("The percentages do not equal 100%\n")
    exit()

filmlines = []
if ".gz" in args.filmlines_file: fl = gzip.open(args.filmlines_file, "rt")
else: fl = open(args.filmlines_file, "rt")
for line in fl:
    filmend = float(line.split()[2])
    filmlines.append(filmend)
fl.close()

total = filmlines[-1]
ideals = [('train',total*(train/100.)),('dev1',total*(dev1/100.)),('dev2',total*(dev2/100.)),('test',total*(test/100.))]
        
dataset = 0
start = 1
numfilms = 0
lastnumfilms = 0
division = []

os.sys.stderr.write("\ntotal number of films = "+str(len(filmlines))+"\n")

for i, lines in enumerate(filmlines):
    numfilms+=1 # count number of films in this dataset
    
    # last dataset - go to end
    if dataset >= len(ideals)-1:
        division.append(int(start))
        os.sys.stderr.write(ideals[-1][0]+" : "+str(int(start))+"-"+str(int(total))+" ("+str(int(total-start+1))+" of an ideal "+str(int(ideals[-1][1]))+", i.e. "+str(round(((total-start)/float(total)*100),2))+"%. "+str(len(filmlines)-lastnumfilms)+" films: up to "+str(len(filmlines))+")\n")   
        break

    # all but last dataset (when reached the ideal number of lines, cut the dataset size here)
    elif ideals[dataset][1]+start<lines:
        division.append(int(start))
        os.sys.stderr.write(ideals[dataset][0]+" : "+str(int(start))+"-"+str(int(lines))+" ("+str(int(lines-start+1))+" of an ideal "+str(int(ideals[dataset][1]))+", i.e. "+str(round(((lines-start+1)/float(total)*100),2))+"%. "+str(numfilms)+" films: up to "+str(i+1)+")\n")
        start = lines+1
        
        dataset+=1 # increment dataset number
        lastnumfilms = lastnumfilms + numfilms # stock the last number of films
        numfilms=0 # reset number of films for next dataset


# divide corpus into three sets and output
# print(division)
trainfp = open(args.train_outfile, "w")
dev1fp = open(args.dev1_outfile, "w")
dev2fp = open(args.dev2_outfile, "w")
testfp = open(args.test_outfile, "w")
j = 0

for i in range(0,int(total)):
    if i+1 < division[1]:
        trainfp.write(str(i+1)+"\n")
    elif i+1 < division[2]:
        dev1fp.write(str(i+1)+"\n")
    elif i+1 < division[3]:
        dev2fp.write(str(i+1)+"\n")
    else:
        testfp.write(str(i+1)+"\n")

trainfp.close()
dev1fp.close()
dev2fp.close()
testfp.close()


        
        
