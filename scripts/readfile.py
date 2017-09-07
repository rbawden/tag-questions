import os, gzip, random

def read_list(filename):
    return read_text_file(filename)


def read_ftl(filename, keep="all", lemma=False):
    if lemma:
        words = {}
    else:
        words = []
    if ".gz" in filename: fp = gzip.open(filename, "rt")
    else: fp = open(filename, "r")
    for line in fp.readlines():
        f,t,l = tuple(line.strip("\n").split("\t"))
        if keep=="all":
            words.append((f,t,l))
        elif keep=="verb":
            if t[0]=="V":
                if lemma:
                    if f not in words: words[f] = []
                    words[f].append(l)
                else: words.append(f)
    return words


def read_text_file(filename):
    lines = []
    if ".gz" in filename:
        with gzip.open(filename, "rt") as fp:
            for line in fp:
                lines.append(line.strip())
    else:
        with open(filename, "r") as fp:
            for line in fp:
                lines.append(line.strip())
    return lines


def read_source_file(filename, gram=1):
    sents = []
    os.sys.stderr.write("reading source sentences, gram = "+str(gram)+"...")
    os.sys.stderr.flush()
    if ".gz" in filename: fp = gzip.open(filename, "rt", encoding="utf-8")
    else: fp = open(filename, "r")
    for line in fp:
        line = "$BEGIN$ "*(gram-1)+line+" $END$"*(gram-1)
        line = line.split()
        grams = []
        if gram==1: sents.append(line)
        else:
            for i in range(len(line)-gram):
                grams.append(tuple(line[i:i+gram-1]))
                sents.append(grams)
    fp.close()
    os.sys.stderr.write("done\n")
    os.sys.stderr.flush()
    return sents

# read file containing lines that indicate tags
def read_tag_file(line_filename, numlines):
    os.sys.stderr.write("reading tag line file...")
    os.sys.stderr.flush()
    y = [False]*numlines
    with open(line_filename, "r", encoding="utf-8") as fp:
        for line in fp:
            if int(line.strip())-1 > len(y): break
            y[int(line.strip())-1] = True
    os.sys.stderr.write("done\n")
    os.sys.stderr.flush()
    return y


def read_g_file(filename, k=100):
    os.sys.stderr.write("Reading g-test file\n")
    words = []
    if ".gz" in filename: fp = gzip.open(filename, "rt")
    else: fp = open(filename, "r")
    for i, line in enumerate(fp.readlines()):
        if i==k: break
        line = line.split("\t")[0]
        line = line.strip('"(')
        line = line.strip('\')"')
        line =  tuple(line.split("', '"))
        words.append(line)#.split("\t")[0].strip())
    fp.close()
    return words

# read the file containing the list of lines automatically identified as tag
# questions
def read_lines(filename):
    lines = []
    if ".gz" in filename: fp = gzip.open(filename, "rt")
    else: fp = open(filename, "r")
    for line in fp:
        lines.append(int(line.strip()))
    fp.close()
    return lines


if __name__=="__main__":
    filename = os.sys.argv[1]

    sents = read_text_file(filename)
    random.shuffle(sents)

    for s, sent in enumerate(sents):
        if s < 250: 
            print(sent)

    
