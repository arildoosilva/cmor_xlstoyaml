import os
from openpyxl import load_workbook


workdir = None


def main(xlsdir):
    """ This script creates YAML files by reading the XLSX CMIP tables
    """
    global workdir
    workdir = xlsdir
    print("")
    for (dirpath, dirnames, filenames) in os.walk(workdir):
        for xls_file in filenames:
            if "xlsx" in xls_file:
                print("Generating file {} using {}".format(xls_file.replace(".xlsx", ".yaml"), xls_file))
                create(xls_file)


def create(xls_file):
    xls_file = '/'.join((workdir, xls_file))  # appends the full path to file
    workbook = load_workbook(xls_file)
    yamlfile = xls_file.replace(".xlsx", ".yaml")
    yamlfile = open(yamlfile, "w")
    for title in workbook.get_sheet_names():
        if title == "description":
            print("\tWriting description")
            yamlfile.write("{}:".format(title) + "\n")
        else:
            print("\tWriting variable {}".format(title))
            yamlfile.write("\t{}:".format(title) + "\n")
        worksheet = workbook[title]
        for row in worksheet.rows:
            line = ""
            for cell in row:
                line = ": ".join((line, str(cell.value)))
            if title == "description":
                tabs = "\t"
            else:
                tabs = "\t\t"
            line = line.replace(": ", tabs, 1).replace("None", "")
            yamlfile.write(line + "\n")
        if title == "description":
            yamlfile.write("\nvariables:\n")
    yamlfile.close()
    print("Done\n")


def clearOut():
    for (dirpath, dirnames, filenames) in os.walk(workdir):
        for xls_file in filenames:
            if "xlsx" in xls_file:
                os.remove("/".join((dirpath, xls_file)))
