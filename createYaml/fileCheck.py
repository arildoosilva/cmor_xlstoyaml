def check(filename):
    f = open(filename, 'r')
    linhas = f.readlines()
    f.close()
    f = open(filename, 'w')
    for linha in linhas:
        linha = linha.replace("'''", "\"")
        linha = linha.replace(",\n", ", ")
        linha = linha.replace("     ", " ")
        f.write(linha)
    f.close()