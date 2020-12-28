# pylint: disable=C0321, C0103, W1203

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

""" # pylint: disable=line-too-long

__PRGM__ = "hackimposition"
__VERSION__ = "1.0.0"
__AUTHOR__ = "PIRX"
__COPYRIGHT__ = "(C) 2020-2021 Pierre Ravenel. GNU GPL 3 or later."

from copy import deepcopy
from itertools import product
import logging
import PyPDF2                   # generic usage
from fpdf import FPDF           # template creation

_TEMPLATE_FILENAME = "template.pdf"
logger = logging.getLogger(__name__)


def mmtopt(val_mm):
    """ mm to pt """
    return 2.834645669 * val_mm


class ImposerPageTemplate:
    """
    Definition de la géometrie
    """

    def __init__(self):
        self.unit = 'pt'                     # self.unit # A3 https://papersizes.io/a/a3
        self.global_w = 1190.7               # Largeur du fichier de sortie
        self.global_h = 842.0                # Hauteur du fichier de sortie

        self.int_margin = mmtopt(5)          # Marge interne
        self.ext_margin = mmtopt(3)          # Marge externe
        self.nb_w = 2                        # Nombre de feuille en largeur
        self.nb_h = 2                        # Nombre de feuille en hauteur

        self.dec_margin = mmtopt(5)          # Marge pour les traits de découpe
        self.dec_line_coef = 0.8             # Espace occupé dans la zone
        self.dec_color = (0, 0, 0)           # Couleur des traits de découpe
        self.dec_keep_overflow = True        # Conservation du surplus de marge

        self.display_debug = False           # Dessine le patron dans le template

        self.scale = None

        self.data_w = None
        self.data_h = None

        # place disponible en plus par cellule
        self.delta_marj_w = None
        self.delta_marj_h = None

        # Marge des cellules
        self.x_margin = None
        self.y_margin = None

        # Taille des cellules
        self.x_size = None
        self.y_size = None


    def compute_internals(self, ini_w, ini_h):
        """ Compute internals """
        # Total Dec Margin
        tdmw = self.dec_margin * (self.nb_w + 1)
        tdmh = self.dec_margin * (self.nb_h + 1)

        # Total Ext Largin
        temw = self.ext_margin * 2
        temh = self.ext_margin * 2

        # Total Cell Space max
        tcswmax = self.global_w - tdmw - temw
        tcshmax = self.global_h - tdmh - temh

        final_wmax = tcswmax / self.nb_w  # W cell max
        final_hmax = tcshmax / self.nb_h  # H cell max

        scale_w = (float(final_wmax) - 2. * self.int_margin) / float(ini_w * 2)
        scale_h = (float(final_hmax) - 2. * self.int_margin) / float(ini_h)
        self.scale = min(scale_w, scale_h)             # scale IMG (maximisation)

        self.data_w = float(ini_w * 2) * self.scale
        self.data_h = float(ini_h) * self.scale

        final_w = self.data_w + self.int_margin * 2      # W cell final
        final_h = self.data_h + self.int_margin * 2       # H cell final

        tcsw = final_w * self.nb_w
        tcsh = final_h * self.nb_h

        # Total delta margin
        tdltmw = self.global_w - tcsw - temw - tdmw
        tdltmh = self.global_h - tcsh - temh - tdmh

        # place disponible en plus par cellule
        self.delta_marj_w = tdltmw / (self.nb_w * 2)
        self.delta_marj_h = tdltmh / (self.nb_h * 2)

        # Marge des cellules
        self.x_margin = self.ext_margin + self.int_margin + \
            self.dec_margin + self.delta_marj_w
        self.y_margin = self.ext_margin + self.int_margin + \
            self.dec_margin + self.delta_marj_h

        # Taille des cellules
        self.x_size = final_w + self.dec_margin + self.delta_marj_w * 2
        self.y_size = final_h + self.dec_margin + self.delta_marj_h * 2

        if self.scale < 0:
            logger.error(f"\tToo small page : scale={self.scale}<0")
        if self.scale != 1:
            logger.warning(
                f"\tW/H={ini_w}/{ini_h}==>{self.data_w/2}/{self.data_h}")
            logger.warning(f"\tSCALE: {self.scale}")

    def compute_real_pos(self, x, y, r):
        """ calcul graphique : index --> position """
        r = 0
        x_offset = self.data_w / 2 * int(x % 2 != 0)
        pos_mat = [(round(x // 2) + r) * self.x_size + x_offset +
                   self.x_margin, (float(y) + r) * self.y_size + self.y_margin]
        # sr = -1 if r else 1
        scale_mat = [self.scale, 0, 0, self.scale]
        mat = scale_mat + pos_mat
        return mat

    def create_template(self, namefile):
        """ Create template pdf from self """
        pdf = FPDF('P', self.unit, (self.global_w, self.global_h))
        pdf.add_page()

        # r = 0

        def xline(y):
            pdf.line(0, y, self.global_w, y)

        def yline(x):
            pdf.line(x, 0, x, self.global_h)

        def cutlinex(y):
            pdf.set_draw_color(0, 0, 255)
            pdf.line(0, y, self.global_w, y)

        def cutliney(x):
            pdf.set_draw_color(0, 0, 255)
            pdf.line(x, 0, x, self.global_h)

        def indlinex(y, r=0.8):
            pdf.set_draw_color(126, 126, 0)
            pdf.dashed_line(0, y, self.global_w, y, 10 * r, 10 * (1 - r))

        def indliney(x, r=0.8):
            pdf.set_draw_color(126, 126, 0)
            pdf.dashed_line(x, 0, x, self.global_h, 10 * r, 10 * (1 - r))

        def hirondelle(x, y, lx, ly):
            """ https://fr.wikipedia.org/wiki/Hirondelle_(imprimerie) """
            pdf.set_draw_color(*self.dec_color)
            pdf.line(x, y + self.dec_line_coef * ly, x,
                     y + ly - self.dec_line_coef * ly)
            pdf.line(x + self.dec_line_coef * lx, y,
                     x + lx - self.dec_line_coef * lx, y)
            C = abs(lx) / 2
            pdf.ellipse(x + lx / 2 - C / 2, y + ly / 2 - C / 2, C, C)

        def display_lines():
            pdf.set_draw_color(255, 0, 0)
            xline(self.ext_margin)
            xline(self.global_h - self.ext_margin)
            yline(self.ext_margin)
            yline(self.global_w - self.ext_margin)

            pdf.set_draw_color(0, 255, 0)
            for x in range(self.nb_w):
                x *= 2
                tab = self.compute_real_pos(x, 0, 0)
                x = tab[4]
                y = tab[5]
                indliney(x - self.delta_marj_w -
                         self.int_margin - self.dec_margin)
                cutliney(x - self.delta_marj_w - self.int_margin)
                indliney(x - self.int_margin, r=0.2)
                indliney(x)
                indliney(x + self.data_w)
                indliney(x + self.data_w + self.int_margin, r=0.2)
                cutliney(x + self.data_w + self.delta_marj_w + self.int_margin)
                indliney(x + self.data_w + self.delta_marj_w +
                         self.int_margin + self.dec_margin)
                indliney(x + self.data_w / 2)

            for y in range(self.nb_w):
                tab = self.compute_real_pos(0, y, 0)
                x = tab[4]
                y = tab[5]
                indlinex(y - self.delta_marj_h -
                         self.int_margin - self.dec_margin)
                cutlinex(y - self.delta_marj_h - self.int_margin)
                indlinex(y - self.int_margin, r=0.2)
                indlinex(y)
                indlinex(y + self.data_h)
                indlinex(y + self.data_h + self.int_margin, r=0.2)
                cutlinex(y + self.data_h + self.delta_marj_h + self.int_margin)
                indlinex(y + self.data_h + self.delta_marj_h +
                         self.int_margin + self.dec_margin)

        def display_hirondelles():
            # for all cell
            for ix, iy in product(range(self.nb_w), range(self.nb_w)):
                tab = self.compute_real_pos(ix * 2, iy, 0)
                x = tab[4]
                y = tab[5]
                realMargH = self.int_margin + \
                    (self.delta_marj_h if self.dec_keep_overflow else 0)
                realMargW = self.int_margin + \
                    (self.delta_marj_w if self.dec_keep_overflow else 0)
                ly = y - realMargH
                hy = y + self.data_h + realMargH
                lx = x - realMargW
                hx = x + self.data_w + realMargW
                L = self.dec_margin
                hirondelle(lx, ly, -L, -L)
                hirondelle(lx, hy, -L, L)
                hirondelle(hx, ly, L, -L)
                hirondelle(hx, hy, L, L)

        if self.display_debug:
            display_lines()

        display_hirondelles()


        pdf.output(namefile, 'F')

    def log(self):
        """ debug data in log """
        logger.debug(
            f"\tOutSize    : W/H = {self.global_w}/{self.global_h} pt")
        logger.debug(f"\tMarg INT : {self.int_margin} pt")
        logger.debug(
            f"\tMarg DEC : {self.dec_margin} pt @ {self.dec_line_coef*100}/100")
        logger.debug(f"\tMarg EXT : {self.ext_margin} pt")
        logger.debug(f"\tOverflow   : {self.dec_keep_overflow}")
        logger.debug(f"\tDebug      : {self.display_debug}")


class ImposerAlgo:
    """
        Algorithme d'imposition
        (i, in_nb_pages) ---> (x, y, outIndexPage)
        in_nb_pages ---> outnb_pages
    """

    def __init__(self, nbW, nbH, method=None):
        self.nbW = nbW                        # nbW
        self.nbH = nbH                        # nbH
        self.K = self.nbW * 2 * self.nbH      # blocks de K pages
        self.nb_in_pages = None
        self.nb_out_pages = None
        method = method if method else None   # TODO

    def compute_internals(self, nb_pages):
        """ Compute internals """
        self.nb_in_pages = nb_pages
        self.nb_out_pages = (nb_pages // 16) * 2 + int((nb_pages % 16) > 0) * 2

    def get_nb_out_pages(self):
        """ return nb out pages """
        return self.nb_out_pages

    def compute_index_pos(self, index):
        """ Retourne la position impose """
        assert index <= self.nb_in_pages - 1
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

        half = index < self.nb_in_pages // 2  # begin or end
        index = index if half else self.nb_in_pages - index - 1  # normalised index
        page_offset, x, y = tab[index % 8] if half else tab[15 - index % 8]
        page = (index // 8) * 2 + page_offset
        assert page < self.nb_out_pages
        r = int(y == 1)  # rotation ?
        return (page, x, y, r)


def _page_size(pdf):
    """ Retourne la taille d'un PyPDF2 """
    return (float(pdf.getPage(0).mediaBox.lowerRight[0] -
                  pdf.getPage(0).mediaBox.lowerLeft[0]),
            float(pdf.getPage(0).mediaBox.upperRight[1] -
                  pdf.getPage(0).mediaBox.lowerRight[1]))


def _read_pdf(filename):
    pdf = PyPDF2.PdfFileReader(filename)
    width, height = _page_size(pdf)
    nb_pages = pdf.getNumPages()
    for titre, elem in pdf.getDocumentInfo().items():
        logger.debug("\t" + titre + ":" + elem)
    logger.debug(f"\tnb_pages: {nb_pages}")
    logger.debug(f"\tWidth:{width} height:{height}")
    return (pdf, width, height, nb_pages)


def impose(template, imposer, infile, outfile):
    """ main func : impose infile """
    logger.info(">>> Config")
    logger.debug(f"\tInfile     : {infile}")
    logger.debug(f"\tOutfile    : {outfile}")
    template.log()

    logger.info(f">>> Parse {infile}")
    inPdf, inWidth, inHeight, in_nb_pages = _read_pdf(infile)

    logger.info(">>> Initialisation template")
    template.compute_internals(inWidth, inHeight)

    logger.info(">>> Initialisation algorithme")
    imposer.compute_internals(in_nb_pages)

    logger.info(f">>> Create template file {_TEMPLATE_FILENAME}")
    template.create_template(_TEMPLATE_FILENAME)

    logger.info(">>> Reopen template file")
    template_pdf, w, h, _ = _read_pdf(_TEMPLATE_FILENAME)
    assert w == template.global_w
    assert h == template.global_h

    logger.info(f">>> Init {outfile}")
    out_pdf = PyPDF2.PdfFileWriter()
    for _ in range(imposer.get_nb_out_pages()):
        out_pdf.addPage(deepcopy(template_pdf.getPage(0)))

    logger.info(">>> Imposition")
    for i in range(imposer.nb_in_pages):
        ipage, x, y, r = imposer.compute_index_pos(i)
        pos = template.compute_real_pos(x, y, r)
        out_pdf.getPage(ipage).mergeTransformedPage(inPdf.getPage(i), pos)
        logger.debug(f"\t[{i}/{imposer.nb_in_pages}]" +
                     f"({i})->(page:{ipage}, x:{x}, y:{y}, r:{r})")

    logger.info(f">>> write out in {outfile}")
    out_pdf.addMetadata(
        {'/Title': f"imposition from {infile}",
         '/Creator': __PRGM__ + " " + __VERSION__ + " " + __COPYRIGHT__})
    with open(outfile, 'wb') as fh:
        out_pdf.write(fh)

    logger.info(f">>> Check {outfile}")
    _read_pdf(outfile)

    logger.info(">>> DONE")
