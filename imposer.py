#!/usr//bin/env python3

"""
    hackabable imposition

|-------------------------------------------------------------------------------
|                                  EXT
|    |------------------------------------------------------------------------
|    |   O     |       O|          DEC         |O       |       0      |
|    |    |--------------------------------------------------|    |---------
|    |    |                        INT                       |    |
|    | -- |    |----------------------------------------|    | -- |    |---
|    |    |    |OVERFLOW|           |          |OVERFLOW|    |    |    |
|    |    |    | MARGIN |    P..    |    P..   | MARGIN |    |    |    |
|    |    |    |        |           |          |        |    |    |    |
|    | -- |    |----------------------------------------|    | -- |    |-
|    |    |                   cellule   INT                  |    |
|    |    |--------------------------------------------------|    |------
|    |   O     |       O|          DEC         |O       |       0
|    |    |--------------------------------------------------|    |---
|    |    |                        INT
|    |
|

"""

import PyPDF2                   # generic usage
from fpdf import FPDF           # template creation
from copy import deepcopy


def mmtopt(mm):
    return 2.834645669 * mm


class Imposer:

    IN_FILE = "maq_cyan.pdf"        # Nom du fichier d'entréee
    OUT_FILE = "out.pdf"            # Nom du fichier de sortie

    UNIT = 'pt'                     # self.UNIT # A3 https://papersizes.io/a/a3
    GLOBAL_W = 1190.7               # Largeur du fichier de sortie
    GLOBAL_H = 842.0                # Hauteur du fichier de sortie

    INT_MARGIN = mmtopt(5)          # Marge interne
    EXT_MARGIN = mmtopt(3)          # Marge externe
    NB_W = 2                        # Nombre de feuille en largeur
    NB_H = 2                        # Nombre de feuille en hauteur

    DEC_MARGIN = mmtopt(5)          # Marge pour les traits de découpe
    DEC_LINE_COEF = 0.8             # Espace occupé dans la zone
    DEC_COLOR = (0, 0, 0)           # Couleur des traits de découpe
    DEC_KEEP_OVERFLOW = True        # Conservation du surplus de marge

    DISPLAY_DEBUG = False           # Dessine le patron dans le template

    def __init__(self):
        pass

    def pageSize(self, pdf):
        """ Retourne la taille d'un PyPDF2 """
        return (float(pdf.getPage(0).mediaBox.lowerRight[0] -
                      pdf.getPage(0).mediaBox.lowerLeft[0]),
                float(pdf.getPage(0).mediaBox.upperRight[1] -
                      pdf.getPage(0).mediaBox.lowerRight[1]))

    def compute0utputPageSize(self, nb_pages):
        return (nb_pages // 16) * 2 + int((nb_pages % 16) > 0) * 2

    def computeInternals(self, iniW, iniH):
        totalDEC_MARGINW = self.DEC_MARGIN * (self.NB_W + 1)
        totalDEC_MARGINH = self.DEC_MARGIN * (self.NB_H + 1)

        totalEXT_MARGINW = self.EXT_MARGIN * 2
        totalEXT_MARGINH = self.EXT_MARGIN * 2

        totalCellSpaceW = float(self.GLOBAL_W - totalDEC_MARGINW - totalEXT_MARGINW)
        totalCellSpaceH = float(self.GLOBAL_H - totalDEC_MARGINH - totalEXT_MARGINH)

        finalWmax = totalCellSpaceW / self.NB_W # W cell max
        finalHmax = totalCellSpaceH / self.NB_H # H cell max

        scaleW =  (float(finalWmax) - 2. * self.INT_MARGIN) / float(iniW * 2)
        scaleH = (float(finalHmax) - 2. * self.INT_MARGIN) / float(iniH)
        self.scale = min(scaleW, scaleH)             # scale IMG

        self.dataW = float(iniW * 2) * self.scale
        self.dataH = float(iniH) * self.scale

        finalW = self.dataW + self.INT_MARGIN * 2      # W cell final
        finalH = self.dataH + self.INT_MARGIN * 2       # H cell final

        # place disponible en plus par cellule
        self.deltaMarginW = float(self.GLOBAL_W - finalW*self.NB_W - totalEXT_MARGINW - totalDEC_MARGINW) / (self.NB_W * 2)
        self.deltaMarginH = float(self.GLOBAL_H - finalH*self.NB_H - totalEXT_MARGINH - totalDEC_MARGINH) / (self.NB_H * 2)

        # Marge des cellules
        self.x_margin = float(self.EXT_MARGIN + self.INT_MARGIN + self.DEC_MARGIN + self.deltaMarginW)
        self.y_margin = float(self.EXT_MARGIN + self.INT_MARGIN + self.DEC_MARGIN + self.deltaMarginH)

        # Taille des cellules
        self.x_size = finalW + self.DEC_MARGIN + self.deltaMarginW * 2
        self.y_size = finalH + self.DEC_MARGIN + self.deltaMarginH * 2

    def computeRealPos(self, x, y, r):
        r = 0;

        pos_mat = [(round(x//2) + r) * self.x_size +  self.dataW/2 * int(x % 2 != 0) + self.x_margin,
                   (float(y) + r) * self.y_size + self.y_margin]
        sr = -1 if r else 1
        scale_mat = [self.scale, 0, 0, self.scale]
        mat = scale_mat + pos_mat
        return mat

    def createTemplate(self, namefile):
        pdf = FPDF('P', self.UNIT, (self.GLOBAL_W, self.GLOBAL_H)) # L; pt, cm, in
        pdf.add_page()

        r = 0

        def xline(y):
            pdf.line(0, y, self.GLOBAL_W, y)

        def yline(x):
            pdf.line(x, 0, x, self.GLOBAL_H)

        def xdline(y, r=1):
            pdf.dashed_line(0, y, self.GLOBAL_W, y, 10*r, 5*r)

        def ydline(x, r=1):
            pdf.dashed_line(x, 0, x, self.GLOBAL_H, 10*r, 5*r)

        def cutlinex(y):
            pdf.set_draw_color(0, 0, 255)
            pdf.line(0, y, self.GLOBAL_W, y)

        def cutliney(x):
            pdf.set_draw_color(0, 0, 255)
            pdf.line(x, 0, x, self.GLOBAL_H)

        def indlinex(y, r=0.8):
            pdf.set_draw_color(126, 126, 0)
            pdf.dashed_line(0, y, self.GLOBAL_W, y, 10*r, 10*(1-r))

        def indliney(x, r=0.8):
            pdf.set_draw_color(126, 126, 0)
            pdf.dashed_line(x, 0, x, self.GLOBAL_H, 10*r, 10*(1-r))

        def hirondelle(x, y, lx, ly):
            """ https://fr.wikipedia.org/wiki/Hirondelle_(imprimerie) """
            pdf.set_draw_color(*self.DEC_COLOR)
            pdf.line(x, y + self.DEC_LINE_COEF*ly, x, y + ly - self.DEC_LINE_COEF*ly)
            pdf.line(x + self.DEC_LINE_COEF*lx, y, x + lx - self.DEC_LINE_COEF*lx, y)
            # pdf.line(x, y + self.DEC_LINE_COEF*ly, x + self.DEC_LINE_COEF*lx, y)
            # pdf.line(x, y + ly - self.DEC_LINE_COEF*ly, x + lx - self.DEC_LINE_COEF*lx, y)
            C = abs(lx)/2
            pdf.ellipse(x + lx/2 - C/2, y + ly/2 - C/2, C, C)

        if self.DISPLAY_DEBUG:
            pdf.set_draw_color(255, 0, 0)
            xline(self.EXT_MARGIN)
            xline(self.GLOBAL_H - self.EXT_MARGIN)
            yline(self.EXT_MARGIN)
            yline(self.GLOBAL_W - self.EXT_MARGIN)

            pdf.set_draw_color(0, 255, 0)
            for x in range(self.NB_W):
                x *= 2
                tab = self.computeRealPos(x, 0, 0)
                s = tab[0]
                x = tab[4]
                y = tab[5]
                indliney(x - self.deltaMarginW - self.INT_MARGIN - self.DEC_MARGIN)
                cutliney(x - self.deltaMarginW - self.INT_MARGIN)
                indliney(x - self.INT_MARGIN, r=0.2)
                indliney(x)
                indliney(x + self.dataW)
                indliney(x + self.dataW + self.INT_MARGIN, r=0.2)
                cutliney(x + self.dataW + self.deltaMarginW + self.INT_MARGIN)
                indliney(x + self.dataW + self.deltaMarginW + self.INT_MARGIN + self.DEC_MARGIN)
                indliney(x + self.dataW/2)

            for y in range(self.NB_W):
                tab = self.computeRealPos(0, y, 0)
                s = tab[0]
                x = tab[4]
                y = tab[5]
                indlinex(y - self.deltaMarginH - self.INT_MARGIN- self.DEC_MARGIN)
                cutlinex(y - self.deltaMarginH - self.INT_MARGIN)
                indlinex(y - self.INT_MARGIN, r=0.2)
                indlinex(y)
                indlinex(y + self.dataH)
                indlinex(y + self.dataH + self.INT_MARGIN, r=0.2)
                cutlinex(y + self.dataH + self.deltaMarginH + self.INT_MARGIN)
                indlinex(y + self.dataH + self.deltaMarginH + self.INT_MARGIN + self.DEC_MARGIN)

        # for all cell
        for ix in range(self.NB_W):
            for iy in range(self.NB_W):
                tab = self.computeRealPos(ix * 2, iy, 0)
                x = tab[4]
                y = tab[5]
                realMarginH = self.INT_MARGIN + (self.deltaMarginH if self.DEC_KEEP_OVERFLOW else 0)
                realMarginW = self.INT_MARGIN + (self.deltaMarginW if self.DEC_KEEP_OVERFLOW else 0)
                ly = y - realMarginH
                hy = y + self.dataH + realMarginH
                lx = x - realMarginW
                hx = x + self.dataW + realMarginW
                L = self.DEC_MARGIN
                hirondelle(lx, ly, -L, -L)
                hirondelle(lx, hy, -L, L)
                hirondelle(hx, ly, L, -L)
                hirondelle(hx, hy, L, L)

        pdf.output(namefile, 'F')

    def computeIndexPos(self, index, nb_pages):
        assert(index <= nb_pages - 1)
        # (page{O 1}, x, y)
        # https://app.lib.uliege.be/guide_catalo/wp-content/uploads/2020/05/Identificationdesformats.pdf
        # Table pliage OK
        tab = [(0, 3, 0), (1, 0, 0),
               (1, 3, 0), (0, 0, 0),
               (0, 0, 1), (1, 3, 1),
               (1, 0, 1), (0, 3, 1),
               (0, 2, 1), (1, 1, 1),
               (1, 2, 1), (0, 1, 1),
               (0, 1, 0), (1, 2, 0),
               (1, 1, 0), (0, 2, 0)]

        # Table Chloe ordre naturel
        tab = [(0, 1, 1), (1, 2, 1),
               (0, 3, 1), (1, 0, 1),
               (0, 1, 0), (1, 2, 0),
               (0, 3, 0), (1, 0, 0),
               (1, 1, 0), (0, 2, 0),
               (1, 3, 0), (0, 0, 0),
               (1, 1, 1), (0, 2, 1),
               (1, 3, 1), (0, 0, 1)]

        mb = index < nb_pages // 2  # begin or end
        index = index if mb else nb_pages - index - 1  # normalised index
        page_offset, x, y = tab[index % 8] if mb else tab[15 - index % 8]
        page = (index // 8)*2 + page_offset
        r = int(y == 1)  # rotation ?
        return (page, x, y, r)

    def impose(self):

        print(f">>> Config")
        print(f"\tInfile     : {self.IN_FILE}")
        print(f"\tOutfile    : {self.OUT_FILE}")
        print(f"\tOutSize    : W/H = {self.GLOBAL_W}/{self.GLOBAL_H} pt")
        print(f"\tMargin INT : {self.INT_MARGIN} pt")
        print(f"\tMargin DEC : {self.DEC_MARGIN} pt @ {self.DEC_LINE_COEF*100}/100")
        print(f"\tMargin EXT : {self.EXT_MARGIN} pt")
        print(f"\tOverflow   : {self.DEC_KEEP_OVERFLOW}")
        print(f"\tDebug      : {self.DISPLAY_DEBUG}")

        print(f">>> Parse {self.IN_FILE}")
        in_pdf = PyPDF2.PdfFileReader(self.IN_FILE)
        width, height = self.pageSize(in_pdf)
        in_size = in_pdf.getNumPages()
        for titre, elem in in_pdf.getDocumentInfo().items():
            print("\t" + titre + ":" + elem)
        print(f"\tnb_pages: {in_size}")
        print(f"\tWidth:{width} height:{height}")

        print(f">>> Initialisation config avec {self.IN_FILE}")
        self.computeInternals(width, height)

        templateFilename = "template.pdf"
        print(f">>> Create template file")
        self.createTemplate(templateFilename)
        print(f"\tW/H={width}/{height} ==> {self.dataW/2}/{self.dataH}")
        print(f"\tSCALE: {self.scale}")

        print(f">>> Reopen template file")
        template_pdf = PyPDF2.PdfFileReader(templateFilename)
        template_page = template_pdf.getPage(0)
        mes_w, mes_h = self.pageSize(template_pdf)  # Check sizes
        assert(mes_w == self.GLOBAL_W)
        assert(mes_h == self.GLOBAL_H)

        print(f">>> Init out_pdf pdf")
        out_pdf = PyPDF2.PdfFileWriter()
        for _ in range(self.compute0utputPageSize(in_size)):
            out_pdf.addPage(deepcopy(template_page))

        print(f">>> Imposition [", end="", flush=True)
        for i in range(in_size):
            ipage, x, y, r = self.computeIndexPos(i, in_size)
            print(".", end='', flush=True)
            pos = self.computeRealPos(x, y, r)
            out_pdf.getPage(ipage).mergeTransformedPage(in_pdf.getPage(i), pos)
        print("] Done")

        print(f">>> write out in {self.OUT_FILE}")
        out_pdf.addMetadata(
            {'/Title': f'{self.IN_FILE}.imposed.pdf',
             '/Producer': "Imposer"})
        with open(self.OUT_FILE, 'wb') as fh:
            out_pdf.write(fh)

        print(f">>> Check {self.OUT_FILE}")
        pdf = PyPDF2.PdfFileReader(self.OUT_FILE)
        width, height = self.pageSize(pdf)
        in_size = pdf.getNumPages()
        for titre, elem in pdf.getDocumentInfo().items():
            print("\t" + titre + ":" + elem)
        print(f"\tnb_pages: {in_size}")
        print(f"\tWidth:{width} height:{height}")

        print(f">>> DONE")


if __name__ == '__main__':
    import argparse
    imposer = Imposer()

    print(__doc__)
    parser = argparse.ArgumentParser(prog="Imposer",
                                     epilog="Toutes les unités sont en pt")
    parser.add_argument('IN_FILE', help="nom du fichier d'entrée")
    parser.add_argument('--OUT_FILE', default="out.pdf", help="nom du fichier de sortie")
    parser.add_argument('--GLOBAL_W', type=float, help="largeur du fichier de sortie")
    parser.add_argument('--GLOBAL_H',type=float,  help="Hauteur du fichier de sortie")
    parser.add_argument('--INT_MARGIN', type=float, help="marge interne")
    parser.add_argument('--EXT_MARGIN', type=float, help="marge externe")
    parser.add_argument('--DEC_MARGIN', type=float, help="marge pour les guides de découpe")
    parser.add_argument('--DEC_LINE_COEF', type=float, help="espace occupé dans la zone de decoupe")
    parser.add_argument('--DEC_KEEP_OVERFLOW', type=int, choices=range(0, 2), help="conservation du surplus de marge en marge INT")
    parser.add_argument('--DISPLAY_DEBUG', type=int, choices=range(0, 2), help="Dessine le patron dans le template")
    parser.parse_args(namespace=imposer)

    imposer.impose()
