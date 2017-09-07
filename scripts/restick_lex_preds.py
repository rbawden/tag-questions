from readfile import *
import argparse, os


def restick_lex(original_preds, lex_preds, lexlines):

    linenumbers = [int(x) for x in lexlines]
    j = 0

    nummisc = len([x for x in original_preds if x=="misc"])
    os.sys.stderr.write(str(nummisc)+"\n")
    os.sys.stderr.write(str(len(lexlines))+"\n")
    os.sys.stderr.write(str(len(lex_preds))+"\n")
    if not (nummisc==len(lexlines)==len(lex_preds)):
        exit("The number of lines is not corrected when sticking lex predictions")
    assert(nummisc==len(lexlines)==len(lex_preds))
    
    for i, pred in enumerate(original_preds):
        if pred=="misc" and i+1 not in linenumbers:
            exit("Problem with lexlines\n")
        if pred=="misc":
            pred=lex_preds[j]
            j += 1
            
        print(pred)
        


if __name__=="__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("original_pred")
    argparser.add_argument("lex_pred")
    argparser.add_argument("lex_linenumbers")
    args = argparser.parse_args()

    original_preds =  read_text_file(args.original_pred)
    lex_preds = read_text_file(args.lex_pred)
    lexlines = read_text_file(args.lex_linenumbers)

    restick_lex(original_preds, lex_preds, lexlines)
    
