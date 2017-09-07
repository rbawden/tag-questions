# classify as producing a tag or not

import re, argparse, os, gzip
from math import log
from readfile import read_list


# tokenised source file (containing tags and non tags)
def read_source_file(filename, gram=1):
    sents = []
    os.sys.stderr.write("Reading source file...")
    os.sys.stderr.flush()
    if ".gz" in filename: fp = gzip.open(filename, "rt", encoding="utf-8")
    else: fp = open(filename, "r", encoding="utf-8")

    for line in fp:
        line = "$BEGIN$ "*(gram-1)+line+" $END$"*(gram-1)
        line = line.split()
        grams = []
        if gram==1: sents.append(line)
        else:
            for i in range(len(line)-1):
                grams.append(tuple(line[i:i+gram]))
                # os.sys.stderr.write(str(grams))
                # input()
            sents.append(grams)
        # print(sents)
        # input()
    os.sys.stderr.write("Done\n")
    fp.close()
    return sents

# read file containing lines that indicate tags
def read_tag_file(line_filename, numlines):
    os.sys.stderr.write("Reading tagline file...")
    os.sys.stderr.flush()
    y = [False]*numlines
    with open(line_filename, "r", encoding="utf-8") as fp:
        for line in fp:
            if int(line.strip())-1 > len(y): break
            y[int(line.strip())-1] = True
    os.sys.stderr.write("Done\n")
    return y


# get vocab
def get_vocab(sents, hapax=-1):
    os.sys.stderr.write("getting vocabulary...")
    os.sys.stderr.flush()
    vocab  = {}
    for sent in sents:
        for word in sent:
            if word not in vocab: vocab[word] = 0
            vocab[word] += 1
    os.sys.stderr.write("done ("+str(len(vocab))+" words in vocabulary)\n")

    # filter very rare ones
    filt_vocab = set([])
    if hapax>0:
        os.sys.stderr.write("filtering words with occs <= "+str(hapax)+"...")
        os.sys.stderr.flush()
        for word in vocab:
            if vocab[word] <= hapax: continue
            else: filt_vocab.add(word)
        os.sys.stderr.write("done ("+str(len(filt_vocab))+" words left)\n")
    else:
        filt_vocab = set(keys(vocab))
    
    return filt_vocab


def filterdict(w2g, maximum):
    
    for i, w in enumerate(sorted(w2g, key=w2g.get)):
        if i > maximum:
            del w2g[w]

def gtest_filter(v, maximum, num_ntag, num_tag, num_sents, s=0.01):
    tmpw2g = {}
    # i = 0
    for w in v:
        # i+=1
        # if i%1000==0: os.sys.stderr.write("\r  "+str(i))
        
        total = float(num_sents + 4 * s)
        p_pres_tag = (v[w][True] + s)/total
        p_pres_ntag = (v[w][False] + s)/total
        p_npres_tag = (num_tag - v[w][True] + s)/total
        p_npres_ntag = (num_ntag - v[w][False] +s)/total
        p_w = p_pres_tag + p_pres_ntag
        p_tag = p_pres_tag + p_npres_tag
        p_nw = p_npres_tag + p_npres_ntag
        p_ntag = p_pres_ntag + p_npres_ntag

        # calculate g2
        g = p_pres_tag * log(p_pres_tag/(p_w*p_tag))
        g += p_npres_tag * log(p_npres_tag/(p_nw*p_tag))
        g += p_pres_ntag * log(p_pres_ntag/(p_w*p_ntag))
        g += p_npres_ntag * log(p_npres_tag/(p_nw*p_ntag))
        g *= 2 * len(v)
        tmpw2g[w] = g
    
    for i, w in enumerate(sorted(tmpw2g, key=tmpw2g.get)):
        if i > maximum:
            del v[w]
    return 

            
def gtest(sents, goldtags, s=0.01, gram=1):
    num_sents = len(sents)
    num_tag = len([x for x in goldtags if x])
    num_ntag = num_sents - num_tag

    goldtags = [True if x =="True" else False for x in goldtags]

    os.sys.stderr.write(str(set(goldtags))+"\n")
    os.sys.stderr.write(str(len(sents))+"\n")
    os.sys.stderr.write(str(len(goldtags))+"\n")
    assert(len(sents)==len(goldtags))
    os.sys.stderr.write("Starting g-tests...\n")
    os.sys.stderr.flush()

    
    # calculate counts for vocab
    os.sys.stderr.write("\nCounting...\n")
    v = {}
    i_tag = 0
    for i, (t, sent) in enumerate(zip(goldtags, sents)):
        if t: i_tag+=1
        for w in set(sent):
            # print(w)
            if w not in v:
                if len(v)%100000==0:os.sys.stderr.write("\r    "+str(len(v)))
                v[w] = {True: 0, False:0}

                # filter here too
                # if len(v)>(6000000/gram): gtest_filter(v, (6000000/gram) - 1000000, i_tag, i+1-i_tag, i+1)
                
            v[w][t] += 1

    # recalculate real values (rather than filtered)
    # for i, (t, sent) in enumerate(zip(tags, sents)):
    #     for w in set(sent):
    #         # print(w)
    #         if w in v:
    #             if "r" not in v[w]:
    #                 if len(v)%100000==0:os.sys.stderr.write("\r    "+str(len(v)))
    #                 v[w] = {True: 0, False:0, "r":1}
    #             v[w][t] += 1
            

    os.sys.stderr.write("\nCalculating probas and g2 ("+str(len(v))+")\n")
    os.sys.stderr.flush()
    w2g = {}
    # calculate probas and gtest
    i = 0
    for w in v:
        i+=1
        if i%1000==0: os.sys.stderr.write("\r  "+str(i))
        
        total = float(num_sents + 4 * s)
        p_pres_tag = (v[w][True] + s)/total
        p_pres_ntag = (v[w][False] + s)/total
        p_npres_tag = (num_tag - v[w][True] + s)/total
        p_npres_ntag = (num_ntag - v[w][False] +s)/total
        p_w = p_pres_tag + p_pres_ntag
        p_tag = p_pres_tag + p_npres_tag
        p_nw = p_npres_tag + p_npres_ntag
        p_ntag = p_pres_ntag + p_npres_ntag

        # calculate g2
        g = p_pres_tag * log(p_pres_tag/(p_w*p_tag))
        g += p_npres_tag * log(p_npres_tag/(p_nw*p_tag))
        g += p_pres_ntag * log(p_pres_ntag/(p_w*p_ntag))
        g += p_npres_ntag * log(p_npres_tag/(p_nw*p_ntag))
        g *= 2 * len(v)

        w2g[w] = g

        if len(w2g)>(6000000/gram): filterdict(w2g, (6000000/gram) - 1000000)
        
        # sumproba = p_pres_tag + p_npres_tag + p_pres_ntag + p_npres_ntag # must be equal to one
        # print(sumproba)

    if len(w2g)>(6000000/gram): filterdict(w2g, (6000000/gram) - 1000000)
    os.sys.stderr.write("\n")
        
    # sort and print
    for w in sorted(w2g, key=w2g.get):
        os.sys.stdout.write(str(w)+"\t"+str(w2g[w])+"\n")

if __name__=="__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("source_file")
    argparser.add_argument("tagnottag")
    argparser.add_argument("gram", default=1, type=int)
    args = argparser.parse_args()
    lang = "cs"

    # os.sys.stderr.write(str(type(args.gram))+str(args.gram))
    source_sents = read_source_file(args.source_file, args.gram)
    gold_lines = read_list(args.tagnottag)

    gtest(source_sents, gold_lines, 0.001, args.gram)


    



