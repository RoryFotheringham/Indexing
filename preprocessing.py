import os
import re

from stemming.porter2 import stem
import xml.etree.ElementTree as ET


def clean_line(line):
    """
    Given a string, this function applies tokenization, stemming, stopping and case folding
    :param line: string of words separated by spaces
    :return: returns a string of words separated by spaces
    """
    stop_words = set()
    with open("englishST.txt", "r", encoding='utf-8') as f:
        for l in f:
            stop_words.add(l[:-1])
    tokens = tokenize(line)
    clean = ""
    for t in tokens:
        if t.lower() not in stop_words:
            clean += f"{stem(t.lower())} "
    return clean[:-1]


def tokenize(line):
    """
    Tokenizes a string of words
    :param line: string of words separated by spaces
    :return: returns list of words
    """
    # support for defining special characters to remove instead of replacing with spaces
    # the list is empty since in my implementation I just split on non-alphanumeric.
    remove_chars = []
    for char in remove_chars:
        line = line.replace(char, '')
    # replace non-alphanumeric chars with a space
    line = re.sub(r'[^A-Za-z0-9 ]+', ' ', line)
    # make sure there is only one space between terms
    line = re.sub(r' +', ' ', line)
    # strip any spaces or newline chars from ends of string
    line = line.strip()
    tokens = line.split(" ")
    return tokens


def parseLectureElem(elem, stop_words):
    for lecture_elem in elem:
        if lecture_elem.tag != "lecture":
            continue
        for subelem in lecture_elem:
            if subelem.tag == "lecture_title":
                continue
            elif subelem.tag == "lecture_pdf_url":
                continue
            elif subelem.tag == "lectureno":
                try:
                    int(subelem.text)
                except:
                    subelem.text = re.sub(u"\u2013", "-", subelem.text).split("-")[0]
                continue

            for slide_elem in subelem:
                slide_no, slide_text = list(slide_elem)
                #print("slide " + slide_no.text)
                if not slide_text.text:
                    continue
                tokens = tokenize(slide_text.text)
                # rint(repr(tokens))
                # print(tokens)
                new_text = ""
                for t in tokens:
                    if t.lower() not in stop_words:
                        new_text += f"{stem(t.lower())} "
                slide_text.text = new_text[:-1]
                # print(subelem.tag, len(subelem.text))
                # print(repr(subelem.text))
    # print("-------")


def preprocess_file_xml(filein, fileout):
    stop_words = set()
    with open("englishST.txt", "r", encoding='utf-8') as f:
        for l in f:
            stop_words.add(l[:-1])
    tree = ET.parse(filein)
    # &#65533;

    #import xml.etree.ElementTree as ET
    #from lxml import etree

    #parser = etree.XMLParser(recover=True, encoding='utf-8')
    #tree = ET.parse(filein, parser=parser)
    # tree = ET.parse(filein, parser=ET.XMLParser(encoding='utf-8'))
    root = tree.getroot()
    # print(root.tag)

    for elem in root:
        # print("=======")
        # print(elem.tag)
        if elem.tag == "source":
            source = elem.text
            continue
        elif elem.tag == "date":
            date = elem.text
            continue
        elif elem.tag == "course":
            continue
        elif elem.tag == "lectures":
            parseLectureElem(elem, stop_words)
        elif elem.tag == "videos":
            continue
    tree.write(fileout)


def preprocess_xml(data_dir, output_dir):
    files = os.scandir(data_dir)
    for f in files:
        inp_dir = data_dir + f.name
        out_dir = output_dir + f.name
        #print(inp_dir)
        preprocess_file_xml(inp_dir, out_dir)
        #exit()
