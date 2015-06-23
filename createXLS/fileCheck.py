def check(filename):
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    f = open(filename, 'w')
    for line in lines:
        line = line.replace("'''", "\"")
        line = line.replace(",\n", ", ")
        line = line.replace("     ", " ")
        f.write(line)
    f.close()