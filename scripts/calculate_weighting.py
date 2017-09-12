import os

def getclass2nb(class_count_file):
    class2nb = {}
    with open(class_count_file, "r", encoding="utf-8") as fp:
        for line in fp:
            if line.strip() == "": continue
            [nb, word] = line.strip().split()
            class2nb[word] = int(nb)
    return class2nb


def calculate_weights(class2nb, p):
    # os.sys.stderr.write(str(class2nb))
    # input()
    if len(class2nb)>0: maxvalue = max(list(class2nb.values()))
    else: maxvalue=0
    for word in class2nb:
        class2nb[word] = ((p*maxvalue)+(1-p)*class2nb[word])/float(class2nb[word])
    return class2nb


def create_bash_command(class2weight):
    bash = ""
    for w, word in enumerate(class2weight):
        if w!=0: bash+=" | "
        word.replace("'", "\'")
        bash += " perl -pe 's/^"+word+"\\s+/"+word+" "+str(class2weight[word])+"\\t/' "
    return bash


if __name__=="__main__":                
    import argparse
    argparser = argparse.ArgumentParser()
    argparser.add_argument("class_counts")
    argparser.add_argument("percentage", type=float)
    args = argparser.parse_args()

    class2nb = getclass2nb(args.class_counts)
    class2weight = calculate_weights(class2nb, args.percentage)
    command = create_bash_command(class2weight)
    print(command)
