import base64
import logging
from io import BytesIO

import numpy as np
import pdfplumber
import requests
import cv2
from shapely.geometry import Polygon

from shapely.strtree import STRtree
from shapely.geometry import box

from utils import ColorThiefWithWhite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrgchartParser:
    def __init__(self, document, page=None):
        with pdfplumber.open(document) as pdf:
            self.page = pdf.pages[page].dedupe_chars()
            logger.info("Opened PDF File")

    def analyze_pdf(self):
        """
        analyze the pdf based on elements in the pdf (found by pdf plumber)
        :return: the found elements
        """
        rect_json = []
        texts = []
        for grp in [self.page.rects, self.page.images]:
            for rect in grp:
                try:
                    text = self.page.crop(
                        (
                            rect["x0"],
                            rect["top"],
                            rect["x1"],
                            rect["bottom"],
                        )
                    ).extract_text(x_tolerance=3, y_tolerance=3)
                    if not text:
                        continue
                    text = text.strip()
                    text_len = len(text)
                    size = (rect["x1"] - rect["x0"]) * (rect["bottom"] - rect["top"])
                    if 0 < text_len < 1000 and size > 400:
                        obj = {
                            "position": [
                                int(rect["x0"]),
                                int(rect["top"]),
                                int(rect["x1"]),
                                int(rect["bottom"]),
                            ],
                            "text": text,
                        }
                        if text not in texts:
                            texts.append(text)
                            rect_json.append(obj)
                except Exception as e:
                    print(e)
        return rect_json

    def analyze_primary_colours(self, entries):
        """
        analyze a list of entries to find their primary colors
        :param entries: list of entries
        :return: list of entries with added primary color
        """
        result = []
        for entry in entries:
            result.append(self.analyze_primary_colour_entry(entry))
        return result

    def analyze_primary_colour_entry(self, entry, n_colors=8):
        """
        analyze the primary colors inside an entry
        :param entry: the entry that should be analyzed
        :param n_colors: number of top colors should be searched for
        :return: updated entry with top n colors
        """
        file_obj = BytesIO()
        self.get_image(entry["position"], resolution=50).save(file_obj, format="PNG")
        file_obj.seek(0)
        color_thief = ColorThiefWithWhite(file_obj)
        colors = list(set(color_thief.get_palette(color_count=n_colors, quality=1)))
        print(colors)
        if len(colors) > 1:
            entry["colors"] = colors
        else:
            entry["colors"] = colors
        return entry

    def remove_to_close_colors(self, colors):
        # iterate trough the list of colors
        # compare the first item to the rest
        # remove all items behind the first item that are a to close match with the first item
        # move to the second item
        # TODO: optimize this a bit
        i = 0
        while i < len(colors) - 2:
            chk_colors = np.array(colors[i:])
            chk_color = np.array(colors[i])
            distances = np.sqrt(np.sum((chk_colors - chk_color) ** 2, axis=1))
            minus = 0
            for distance in distances:
                if distance < 10:
                    index = np.where(distances == distance)
                    print(index)
                    if len(colors) > index[0][0] + 1 - minus:
                        del colors[index[0][0] + 1 - minus]
                    else:
                        break
                    minus += 1
            i += 1

        return colors

    def get_image(self, position, resolution=200):
        """
        get part of the pdf rendered as an image
        :param position: the area that should be rendered
        :param resolution: the resolution (see pdfplumber)
        :return: the image as a bytes object
        """
        return self.page.crop(position).to_image(resolution=resolution).original

    def analyze_opencv(self):
        """
        analyze pdf by taking an image and searching for conturs with the help of opencv (this is an alternative strategy)
        :return: the found elements
        """
        img = np.array(self.page.to_image().original)
        imgGry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        ret, thrash = cv2.threshold(imgGry, 205, 255, cv2.CHAIN_APPROX_NONE)
        contours, hierarchy = cv2.findContours(
            thrash, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
        )
        texts = []
        rect_json = []
        for contour in contours:
            approx = cv2.approxPolyDP(
                contour, 0.01 * cv2.arcLength(contour, True), True
            )

            x = approx.ravel()[0]
            y = approx.ravel()[1] - 5
            x, y, w, h = cv2.boundingRect(approx)
            size = w * h
            if 0 < len(approx) < 25 and size > 900:
                text = self.page.crop(
                    (
                        x,
                        y,
                        x + w,
                        y + h,
                    )
                ).extract_text(x_tolerance=3, y_tolerance=3)
                if text:
                    obj = {
                        "position": [int(x), int(y), int(x + w), int(y + h)],
                        "text": text.strip(),
                    }
                    if len(text) > 0 and len(text) < 1000:
                        texts.append(text)
                        rect_json.append(obj)
        return rect_json


def deduplicate_entries(entries):
    """
    thakes a list of entries and tries to find out if any of those is a superset of multiple other entries (by using an strtree)
    :param entries: list of entries
    :return: filtered list of entries
    """
    polygons = [box(*entry["position"]) for entry in entries]
    stree = STRtree(polygons)
    new_entries = []
    for entry in entries:
        cur_e = box(*entry["position"])
        covers_element = False
        for e in stree.query(cur_e):
            if cur_e.covers(e) and cur_e != e:
                print(f"{cur_e} covers {e}")
                covers_element = True
                break
        if not covers_element:
            new_entries.append(entry)
    return new_entries
