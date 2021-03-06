import time
import os
import shutil
import stat
import glob

permissions = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP |\
              stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH

def get_conversion_status(root='/stornext/online13/ocean/simulations/CMIP/CMIP5/output/INPE/BESM-OA2-3/'):
    decades30 = ['decadal1960', 'decadal1980', 'decadal2005']
    decades10 = ['decadal1965', 'decadal1970', 'decadal1975', 'decadal1985',
                 'decadal1990', 'decadal1995', 'decadal2000']
    decades = decades30 + decades10
    
    frequency = 'day'
    condition = 'r{0}i1p{1}'
    variables = [('atmos', 'zg', 40), ('ocean', 'tossq', 42), ('land', 'mrsos', 2)]

    text_lines = []

    for decade in decades:
        decade_expected = 120.
        if decade in decades30:
            decade_expected = 360.
        for r in range(1,11): #r1 a r10
            for p in range(1,3): #p1 e p2
                cond = condition.format(r, p)
                cond_total = 0.
                cond_weights = 0.
                for var in variables:
                    directory = os.path.join(root, decade, frequency, var[0], var[1], cond)
                    try:
                        ls = os.listdir(directory)
                    except:
                        continue
                    else:
                        var_total = len(ls)
                        progress = str(var_total / decade_expected)
                        line = ' '.join([decade, cond, var[0], str(var_total), str(decade_expected), progress, '\n'])
                        text_lines.append(line)
                        
                        for output in ls:
                            data = output.split('_')
                            data[3] = data[3][9:]
                            line = ' '.join(['\t',
                                "".join(data[3:5] + [var[0][0]]),
                                "".join(data[5].split('-')[0][:6]), '\n'])
                            text_lines.append(line)


    DEST_PATH = 'conversion_nodes.txt'
    DEST_FILE = open(DEST_PATH, 'w')
    DEST_FILE.writelines(text_lines)
    DEST_FILE.close()
    os.chmod(DEST_PATH, permissions)


def get_conversion_status_full(root='/stornext/online13/ocean/simulations/CMIP/CMIP5/output/INPE/BESM-OA2-3/'):
    decades30 = ['decadal1960', 'decadal1980', 'decadal2005']
    decades10 = ['decadal1965', 'decadal1970', 'decadal1975', 'decadal1985',
                 'decadal1990', 'decadal1995', 'decadal2000']
    decades100 = decades30
    decades = decades30 + decades10

    conds100 = ('r1i1p1')

    frequency = ('3hr', '6hr', 'day', 'mon', 'monClim')
    realms = ('atmos', 'ocean', 'land')
    #variables = [('atmos', 'zg', 40), ('ocean', 'tossq', 42), ('land', 'mrsos', 2)]
    condition = 'r{0}i{1}p{2}'

    text_lines = []

    for decade in decades:
        i = 1
        result = {}
        for r in range(1,11): #r1 a r10
            for p in range(1,3): #p1 e p2
                cond = condition.format(r, i, p)
                for freq in frequency:
                    for realm in realms:
                        basedir = os.path.join(root, decade, freq, realm)
                        try:
                           variables = os.listdir(basedir)
                        except OSError:
                           variables = []

                        for var in variables:
                            directory = os.path.join(basedir, var, cond)
                            try:
                                ls = os.listdir(directory)
                            except OSError:
                                continue
                            else:
                                exp_completed = []
                                for output in sorted(ls):
                                    data = output.split('_')
                                    try:
                                        exp_completed.append(int(data[5].split('-')[0][:6]))
                                    except ValueError:
                                        print os.path.join(directory, output)
                                        continue
                                exp_completed = set(exp_completed)
                                try:
                                    completed = result[cond+realm[0]]
                                except KeyError:
                                    completed = exp_completed
                                result[cond+realm[0]] = completed & exp_completed

        for exp, value in sorted(result.iteritems()):
            cond = exp[:-1]
            realm = [r for r in realms if r[0] is exp[-1:]][0]

            decade_expected = 120.
            if decade in decades30:
                decade_expected = 360.
            if cond in conds100 and decade in decades100:
                decade_expected = 1200.
            start = int(decade[-4:]) + 1
            end = int(start + decade_expected / 12)
            all = set([y * 100 + m for y in range(start, end) for m in range(1,13)])

            var_total = len(value)
            progress = str(var_total / decade_expected)
            line = ' '.join([decade, exp[:-1], realm, str(var_total), str(decade_expected), progress, '\n'])
            text_lines.append(line)

            for step in sorted(all - value):
                line = " ".join(['\t', decade[-2:] + exp, str(step), '\n'])
                text_lines.append(line)

    DEST_PATH = 'conversion_nodes_full.txt'
    DEST_FILE = open(DEST_PATH, 'w')
    DEST_FILE.writelines(text_lines)
    DEST_FILE.close()
    os.chmod(DEST_PATH, permissions)


if __name__ == "__main__":
    import sys
    get_conversion_status_full(sys.argv[1])
