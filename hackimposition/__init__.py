

"""

    Perform an imposition on the PDF file given in argument.

# Imposition

Imposition consists in the arrangement of the printed product’s pages on the printer’s sheet, in order to obtain faster printing, simplify binding and reduce paper waste (source: http://en.wikipedia.org/wiki/Imposition).

# Printing

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

import hackimposition
import logging

__PRGM__ = "hackimposition"
__VERSION__ = "1.0.0"
__AUTHOR__ = "PIRX"
__COPYRIGHT__ = "(C) 2020-2021 Pierre Ravenel. GNU GPL 3 or later."

LOGGER = logging.getLogger(hackimposition.__name__)

import PyPDF2                   # generic usage
from fpdf import FPDF           # template creation
from copy import deepcopy

_TEMPLATE_FILENAME = "template.pdf"

def mmtopt(mm):
    return 2.834645669 * mm

class ImposerPageTemplate:
    """
    Definition de la géometrie
    """
    def __init__(self):
        self.UNIT = 'pt'                     # self.UNIT # A3 https://papersizes.io/a/a3
        self.GLOBAL_W = 1190.7               # Largeur du fichier de sortie
        self.GLOBAL_H = 842.0                # Hauteur du fichier de sortie

        self.INT_MARGIN = mmtopt(5)          # Marge interne
        self.EXT_MARGIN = mmtopt(3)          # Marge externe
        self.NB_W = 2                        # Nombre de feuille en largeur
        self.NB_H = 2                        # Nombre de feuille en hauteur

        self.DEC_MARGIN = mmtopt(5)          # Marge pour les traits de découpe
        self.DEC_LINE_COEF = 0.8             # Espace occupé dans la zone
        self.DEC_COLOR = (0, 0, 0)           # Couleur des traits de découpe
        self.DEC_KEEP_OVERFLOW = True        # Conservation du surplus de marge

        self.DISPLAY_DEBUG = False           # Dessine le patron dans le template

    def computeInternals(self, iniW, iniH):
        self.iniW = iniW
        self.iniH = iniH

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
        self.scale = min(scaleW, scaleH)             # scale IMG (maximisation)

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

        if(self.scale < 0):
            LOGGER.error(f"\tToo small page : scale={self.scale}<0")
        if(self.scale != 1):
            LOGGER.warning(f"\tW/H={self.iniW}/{self.iniH} ==> {self.dataW/2}/{self.dataH}")
            LOGGER.warning(f"\tSCALE: {self.scale}")

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

    def log(self):
        LOGGER.debug(f"\tOutSize    : W/H = {self.GLOBAL_W}/{self.GLOBAL_H} pt")
        LOGGER.debug(f"\tMargin INT : {self.INT_MARGIN} pt")
        LOGGER.debug(f"\tMargin DEC : {self.DEC_MARGIN} pt @ {self.DEC_LINE_COEF*100}/100")
        LOGGER.debug(f"\tMargin EXT : {self.EXT_MARGIN} pt")
        LOGGER.debug(f"\tOverflow   : {self.DEC_KEEP_OVERFLOW}")
        LOGGER.debug(f"\tDebug      : {self.DISPLAY_DEBUG}")


class ImposerAlgo:
    """
        Algorithme d'imposition
        (i, inNbPages) ---> (x, y, outIndexPage)
        inNbPages ---> outNbPages
    """
    def __init__(self, nbW, nbH, method=None):
        self.nbW = nbW                        # nbW
        self.nbH = nbH                        # nbH
        self.K = self.nbW * 2 * self.nbH      # blocks de K pages

    def computeInternals(self, nb_pages):
        self.nbInPages = nb_pages
        self.nbOutPages = (nb_pages // 16) * 2 + int((nb_pages % 16) > 0) * 2

    def getNbOutPages(self):
        return self.nbOutPages

    def computeIndexPos(self, index):
        """ Retourne la position impose """
        assert(index <= self.nbInPages - 1)
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

        mb = index < self.nbInPages // 2  # begin or end
        index = index if mb else self.nbInPages - index - 1  # normalised index
        page_offset, x, y = tab[index % 8] if mb else tab[15 - index % 8]
        page = (index // 8)*2 + page_offset
        assert(page < self.nbOutPages)
        r = int(y == 1)  # rotation ?
        return (page, x, y, r)

def _pageSize(pdf):
    """ Retourne la taille d'un PyPDF2 """
    return (float(pdf.getPage(0).mediaBox.lowerRight[0] -
                  pdf.getPage(0).mediaBox.lowerLeft[0]),
            float(pdf.getPage(0).mediaBox.upperRight[1] -
                  pdf.getPage(0).mediaBox.lowerRight[1]))

def _readPdf(filename):
    pdf = PyPDF2.PdfFileReader(filename)
    width, height = _pageSize(pdf)
    nbPages = pdf.getNumPages()
    for titre, elem in pdf.getDocumentInfo().items():
        LOGGER.debug("\t" + titre + ":" + elem)
    LOGGER.debug(f"\tnb_pages: {nbPages}")
    LOGGER.debug(f"\tWidth:{width} height:{height}")
    return (pdf, width, height, nbPages)

def impose(template, imposer, infile, outfile):
    IN_FILE = infile                # Nom du fichier d'entréee
    OUT_FILE = outfile              # Nom du fichier de sortie

    LOGGER.info(f">>> Config")
    LOGGER.debug(f"\tInfile     : {IN_FILE}")
    LOGGER.debug(f"\tOutfile    : {OUT_FILE}")
    template.log()

    LOGGER.info(f">>> Parse {IN_FILE}")
    inPdf, inWidth, inHeight, inNbPages = _readPdf(IN_FILE)

    LOGGER.info(f">>> Initialisation template")
    template.computeInternals(inWidth, inHeight)

    LOGGER.info(f">>> Initialisation algorithme")
    imposer.computeInternals(inNbPages)

    LOGGER.info(f">>> Create template file")
    template.createTemplate(_TEMPLATE_FILENAME)

    LOGGER.info(f">>> Reopen template file")
    templatePdf, w, h, _ = _readPdf(_TEMPLATE_FILENAME)
    templatePage = templatePdf.getPage(0)
    assert(w == template.GLOBAL_W)
    assert(h == template.GLOBAL_H)

    LOGGER.info(f">>> Init outPdf pdf")
    outPdf = PyPDF2.PdfFileWriter()
    for _ in range(imposer.getNbOutPages()):
        outPdf.addPage(deepcopy(templatePage))

    LOGGER.info(f">>> Imposition")
    for i in range(imposer.nbInPages):
        ipage, x, y, r = imposer.computeIndexPos(i)
        pos = template.computeRealPos(x, y, r)
        outPdf.getPage(ipage).mergeTransformedPage(inPdf.getPage(i), pos)
        LOGGER.debug(f"\t[{i}/{imposer.nbInPages}]" +
                     f"({i})->(page:{ipage}, x:{x}, y:{y}, r:{r})")


    LOGGER.info(f">>> write out in {OUT_FILE}")
    outPdf.addMetadata(
        {'/Title': f'{IN_FILE}.imposed.pdf',
         '/Producer': "Imposer"})
    with open(OUT_FILE, 'wb') as fh:
        outPdf.write(fh)

    LOGGER.info(f">>> Check {OUT_FILE}")
    _readPdf(OUT_FILE)

    LOGGER.info(f">>> DONE")
