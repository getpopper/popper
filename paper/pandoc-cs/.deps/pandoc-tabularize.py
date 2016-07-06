# taken from https://groups.google.com/d/topic/pandoc-discuss/RUC-tuu_qf0

import pandocfilters as pf

def latex(s):
    return pf.RawBlock('latex', s)

def inlatex(s):
    return pf.RawInline('latex', s)

def tbl_caption(s):
    return pf.Para([inlatex(r'\caption{')] + s + [inlatex('}')])

def tbl_alignment(s):
    aligns = {
        "AlignDefault": 'l',
        "AlignLeft": 'l',
        "AlignCenter": 'c',
        "AlignRight": 'r',
    }
    return ''.join([aligns[e['t']] for e in s])

def tbl_headers(s):
    result = s[0][0]['c'][:]
    for i in range(1, len(s)):
        result.append(inlatex(' & '))
        result.extend(s[i][0]['c'])
    result.append(inlatex(r' \\\midrule'))
    return pf.Para(result)

def tbl_contents(s):
    result = []
    for row in s:
        para = []
        for col in row:
            para.extend(col[0]['c'])
            para.append(inlatex(' & '))
        result.extend(para)
        result[-1] = inlatex(r' \\' '\n')
    return pf.Para(result)

def do_filter(k, v, f, m):
    if k == "Table":
        return [latex(r'\begin{table}[ht]' '\n' r'\centering' '\n'),
                tbl_caption(v[0]),
                latex(r'\begin{tabular}{@{}%s@{}}' % tbl_alignment(v[1]) +
                      ('\n' r'\toprule')),
                tbl_headers(v[3]),
                tbl_contents(v[4]),
                latex(r'\bottomrule' '\n' r'\end{tabular}'),
                latex(r'\end{table}')]


if __name__ == "__main__":
    pf.toJSONFilter(do_filter)

