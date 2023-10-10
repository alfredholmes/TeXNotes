import sys, re


def main(filename):
    with open(filename, 'r') as f:
        textfile = f.read()

    #standard links
    regex = "\[\[([A-Za-z0-9\-\_]+)\]\]"
    text = re.sub(regex, lambda m: f"\\excref{{{m.group(1)}}}", textfile)

    regex = "\[\[([A-Za-z0-9\-\_]+)\#([A-Za-z0-9\-\_]+)\]\]"
    text = re.sub(regex, lambda m: f"\\excref[{m.group(2)}]{{{m.group(1)}}}", text)
    

    regex = "\[\[([A-Za-z0-9\-\_]+)\|([^]]+)\]\]"
    text = re.sub(regex, lambda m: f"\\exhyperref{{{m.group(1)}}}{{{m.group(2)}}}", text)
    
    regex = "\[\[([A-Za-z0-9\-\_]+)\#([A-Za-z0-9\-\_]+)\|([^]]+)\]\]"
    text = re.sub(regex, lambda m: f"\\exhyper[{m.group(2)}]{{{m.group(1)}}}{{{m.group(3)}}}", text)
     
    with open('preprocessed.md', 'w') as f:
        f.write(text)

if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except IndexError:
        print('please pass the filename as a command line argument')
