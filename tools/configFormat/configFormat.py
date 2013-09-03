import os

if __name__ == "__main__":
    try:
        os.mkdir('output')
    except:
        pass
    indir = os.getcwd() + "/input"
    for a, b, c in os.walk(indir):
        if (a==indir):
            for filename in c:
                filename1, ext = filename.split(".")
                if ext != "csv":
                    raise Exception("csv only")
                with open("input/"+filename) as f:
                    with open("output/"+filename1+".txt", "w") as fout:
                        for i, line in enumerate(f):
                            if i != 0:
                               fout.write("\n") 
                            if line[-2:] == "\r\n":
                                line = line[:-2]
                            fout.write(line)
