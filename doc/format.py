#!/usr/bin/python
import sys
LINELEN = 80

def center(s, linelen):
    return default(s.center(linelen), linelen)

def default(s, linelen):
    s = s + " " * (linelen - len(s))
    return " | " + s + " |\n"

def line(s, linelen):
    return " +-" + "-" * linelen + "-+\n"

ops = {"": default, "*": center, "-": line, ">": lambda s, l: s[1:] + "\n"}

def main():
    if len(sys.argv) != 3:
        print """usage: %s input output
String prefixes:
* Centered Text
- Line
> Raw""" % sys.argv[0]
    else:
        i = open(sys.argv[1], "r")
        lines = map(str.rstrip, i.readlines())
        linelen = max(map(len, lines))
        o = open(sys.argv[2], "w")
        for line in lines:
            if line and line[0] in ops:
                line = ops[line[0]](line[1:], linelen)
            elif line.startswith("include: "):
                line = open(line[9:], "r").read()
            else:
                line = ops[""](line, linelen)
            o.write(line)
        i.close()
        o.close()

if __name__ == "__main__":
    main()
